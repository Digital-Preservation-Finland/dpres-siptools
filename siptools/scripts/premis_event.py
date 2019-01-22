"""Command line tool for creating premis events"""
import sys
import os
from uuid import uuid4
import argparse

import premis
import mets
import xml_helpers.utils

from siptools.xml.premis import PREMIS_EVENT_TYPES, PREMIS_EVENT_OUTCOME_TYPES
from siptools.utils import AmdCreator, encode_path, encode_id


def parse_arguments(arguments):
    """Create arguments parser and return parsed command line argumets"""

    def _list2str(lst):
        """Create a human readable list of words from list of strings.

        :param lst: list of strings
        :returns: list formatted as single string
        """
        first_words = ['"' + string + '"' for string in lst[:-1]]
        last_word = '"' + lst[-1] + '"'
        return ', '.join(first_words) + ', and ' + last_word

    parser = argparse.ArgumentParser(
        description=(
            "Create METS document that contains PREMIS event element. Another "
            "METS document that contains PREMIS agent element is created if "
            "optional parameters \"agent_type\" and \"agent_name\" are used. "
            "The PREMIS agent element is linked to PREMIS event element by "
            "unique identifier. The digiprovMD elements get identifiers based "
            "on the METS document filename. "
        )
    )
    parser.add_argument('event_type',
                        type=str,
                        metavar='event_type',
                        choices=PREMIS_EVENT_TYPES,
                        help=('Event type. Possible values are: ' +
                              _list2str(PREMIS_EVENT_TYPES)))
    parser.add_argument('event_datetime',
                        type=str,
                        help='Event datetime formatted as yyyy-mm-ddThh:mm:ss')
    parser.add_argument('--event_detail',
                        dest='event_detail',
                        type=str,
                        required=True,
                        help='Event detail')
    parser.add_argument('--event_outcome',
                        metavar='EVENT_OUTCOME',
                        choices=PREMIS_EVENT_OUTCOME_TYPES,
                        dest='event_outcome',
                        type=str,
                        required=True,
                        help=('Event outcome type. Possible values are: ' +
                              _list2str(PREMIS_EVENT_OUTCOME_TYPES)))
    parser.add_argument('--event_outcome_detail',
                        dest='event_outcome_detail',
                        type=str,
                        help='Event outcome detail')
    parser.add_argument('--workspace',
                        dest='workspace',
                        type=str,
                        default='./workspace',
                        help=("Directory where files are created. Default "
                              "is ./workspace"))
    parser.add_argument('--agent_name',
                        dest='agent_name',
                        required='--agent_type' in sys.argv,
                        type=str,
                        help='Agent name')
    parser.add_argument('--agent_type',
                        dest='agent_type',
                        required='--agent_name' in sys.argv,
                        type=str,
                        help='Agent type')
    parser.add_argument('--stdout',
                        action='store_true',
                        help='Print output to stdout')
    parser.add_argument('--event_target',
                        dest='event_target',
                        type=str,
                        help=('Target for the event. Default is the root of '
                              'digital objects.'))

    return parser.parse_args(arguments)


def main(arguments=None):
    """The main method for premis_event.

    :param arguments: list of commandline arguments
    :returns: 0
    """

    args = parse_arguments(arguments)

    if args.agent_name or args.agent_type:
        agent_identifier = str(uuid4())
        agent = create_premis_agent(args.agent_name,
                                    args.agent_type, agent_identifier)

        agent_creator = PremisCreator(args.workspace)
        agent_creator.add_md(agent, args.event_target)
        agent_creator.write(mdtype="PREMIS:AGENT", stdout=args.stdout)

        if args.stdout:
            print xml_helpers.utils.serialize(agent)
    else:
        agent_identifier = None

    event = create_premis_event(
        args.event_type,
        args.event_datetime,
        args.event_detail,
        args.event_outcome,
        args.event_outcome_detail,
        agent_identifier
    )
    creator = PremisCreator(args.workspace)
    creator.add_md(event, args.event_target)
    creator.write(mdtype="PREMIS:EVENT", stdout=args.stdout)

    return 0


class PremisCreator(AmdCreator):
    """Subclass of AmdCreator, which generates PREMIS event
    or agent metadata.
    """

    def write(self, mdtype="PREMIS", mdtypeversion="2.3",
              section="digiprovmd", stdout=False):
        super(PremisCreator, self).write(
            mdtype=mdtype, mdtypeversion=mdtypeversion, section=section)


def create_premis_agent_file(workspace, event_type, agent_name, agent_type,
                             agent_identifier, event_target=None):
    """Creates `<event_type>-agent.xml` file. If path to target file is given
    as `event_target` parameter, the URL-encoded path is used as filename
    prefix. The file is METS XML file that contains PREMIS agent element inside
    digiprovMD element. The ID attribute of digiprovMD is hashed from the
    filename.

    :param workspace: path to directory where file is created
    :param event_type: event type (for filename)
    :param agent_name: PREMIS agentName
    :param agent_type: PREMIS agentType
    :param agent_identifier: PREMIS agentIdentifierValue
    :param event_target: event target file (for filename)
    :returns: output file path and METS XML element object
    """
    output_filename = '%s-agent.xml' % (event_type)
    if event_target:
        output_filename = '%s-%s' % (event_target, output_filename)
    output_filename = encode_path(output_filename)

    agent_id = encode_id(output_filename)

    premis_agent = create_premis_agent(agent_name,
                                       agent_type,
                                       agent_identifier)

    agent_mets = _create_mets(premis_agent, agent_id, 'PREMIS:AGENT')
    _write_mets(agent_mets, os.path.join(workspace, output_filename))

    return (os.path.join(workspace, output_filename),
            agent_mets)


def create_premis_event_file(workspace, event_type, event_datetime,
                             event_detail, event_outcome, event_outcome_detail,
                             event_target=None, agent_identifier=None):
    """Creates `<event_type>-event.xml` file. If path to target file is given
    as `event_target` parameter, the URL-encoded path is used as filename
    prefix. The file is METS XML file that contains PREMIS event element inside
    digiprovMD element. The ID attribute of digiprovMD is hashed from the
    filename.

    :param workspace: path to directory where file is created
    :param event_type: PREMIS eventType
    :param event_datetime: PREMIS eventDateTime
    :param event_detail: PREMIS eventDetail
    :param event_outcome: PREMIS eventOutcome
    :param event_outcome_detail: PREMIS eventOutcomeDetail
    :param agent_identifier: PREMIS linkingAgentIdentifierValue
    :param event_target: event target file (for filename)
    :returns: output file path and METS XML element object
    """
    output_filename = '%s-event.xml' % event_type
    if event_target:
        output_filename = '%s-%s' % (event_target, output_filename)
    output_filename = encode_path(output_filename)

    event_id = encode_id(output_filename)

    premis_event = create_premis_event(
        event_type, event_datetime, event_detail,
        event_outcome, event_outcome_detail, agent_identifier
    )

    event_mets = _create_mets(premis_event, event_id, 'PREMIS:EVENT')
    _write_mets(event_mets, os.path.join(workspace, output_filename))

    return (os.path.join(workspace, output_filename),
            event_mets)


def _write_mets(mets_element, output_file):
    """Write METS XML element to file.

    :param mets_element: METS XML element
    :param output: output file path
    :returns: ``None``
    """

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w+') as output:
        output.write(xml_helpers.utils.serialize(mets_element))


def _create_mets(premis_element, digiprovmd_id, mdtype):
    """Creates a METS XML element that contains PREMIS element

    :param premis_element: PREMIS element
    :param digiprovmd_id: ID attribute of digiprovMD element
    :param mdtype: MDTYPE of mdWrap element
    :returns: METS XML element
    """
    xmldata = mets.xmldata(child_elements=[premis_element])
    mdwrap = mets.mdwrap(mdtype, '2.3', child_elements=[xmldata])
    digiprovmd = mets.digiprovmd(digiprovmd_id, child_elements=[mdwrap])
    amdsec = mets.amdsec(child_elements=[digiprovmd])
    _mets = mets.mets(child_elements=[amdsec])

    return _mets


def create_premis_agent(agent_name, agent_type, agent_identifier):
    """Creates METS digiprovMD element that contains PREMIS agent element with
    unique identifier.

    :param agent_name: content of PREMIS agentName element
    :param agent_type: content of PREMIS agentType element
    :param agent_identifier: content of PREMIS agentIdentifierValue element
    :returns: PREMIS event XML element
    """
    agent_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=agent_identifier, prefix='agent'
    )
    premis_agent = premis.agent(agent_identifier, agent_name, agent_type)

    return premis_agent


def create_premis_event(event_type, event_datetime, event_detail,
                        event_outcome, event_outcome_detail, agent_identifier):
    """Creates METS digiprovMD element that contains PREMIS event element.
    Linking agent identifier element is added to PREMIS event element, if agent
    identifier is provided as parameter.

    :param event_type: Event type
    :param event_datetime: Event time
    :param event_detail: Event details
    :param event_outcome: Event outcome ("success" or "failure")
    :param event_outcome_detail: Event outcome description
    :param agent_identifier: PREMIS agent identifier or ``None``
    :returns: PREMIS event XML element
    """
    event_identifier = premis.identifier(
        identifier_type='UUID',
        identifier_value=str(uuid4()),
        prefix='event'
    )

    premis_event_outcome = premis.outcome(event_outcome,
                                          event_outcome_detail)

    child_elements = [premis_event_outcome]

    # Create linkingAgentIdentifier element if agent identifier is provided
    if agent_identifier is not None:
        linking_agent_identifier = premis.identifier(
            identifier_type='UUID',
            identifier_value=agent_identifier,
            prefix='linkingAgent'
        )
        child_elements.append(linking_agent_identifier)

    premis_event = premis.event(event_identifier, event_type,
                                event_datetime, event_detail,
                                child_elements=child_elements)

    return premis_event


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
