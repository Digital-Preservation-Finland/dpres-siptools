"""Command line tool for creating premis events"""
import sys
import os
from uuid import uuid4
import click

import premis
import mets
import xml_helpers.utils

from siptools.xml.premis import PREMIS_EVENT_TYPES, PREMIS_EVENT_OUTCOME_TYPES
from siptools.utils import AmdCreator, encode_path, encode_id


def _list2str(lst):
    """Create a human readable list of words from list of strings.

    :param lst: list of strings
    :returns: list formatted as single string
    """
    first_words = ['"' + string + '"' for string in lst[:-1]]
    last_word = '"' + lst[-1] + '"'
    return ', '.join(first_words) + ', and ' + last_word


@click.command()
@click.argument('event_type',
                type=click.Choice(PREMIS_EVENT_TYPES))
@click.argument('event_datetime', required=True,
                type=str)
@click.option('--workspace',
              type=click.Path(exists=True),
              default='./workspace',
              metavar='<WORKSPACE PATH>',
              help=("Directory where files are created. Defaults "
                    "to ./workspace/"))
@click.option('--event_target',
              type=str,
              metavar='<EVENT TARGET PATH>',
              help=('Target for the event. Default is the root of '
                    'digital objects.'))
@click.option('--event_detail',
              type=str, required=True,
              metavar='<EVENT DETAIL>',
              help='Short information about the event')
@click.option('--event_outcome',
              type=click.Choice(PREMIS_EVENT_OUTCOME_TYPES),
              required=True,
              metavar='<EVENT OUTCOME>',
              help=('Event outcome type. Possible values are: ' +
                    _list2str(PREMIS_EVENT_OUTCOME_TYPES)))
@click.option('--event_outcome_detail',
              type=str,
              metavar='<EVENT OUTCOME DETAIL>',
              help='Detailed information about the event outcome.')
@click.option('--agent_name',
              required='--agent_type' in sys.argv,
              type=str,
              metavar='<AGENT NAME>',
              help='Agent name')
@click.option('--agent_type',
              required='--agent_name' in sys.argv,
              type=str,
              metavar='<AGENT TYPE>',
              help='Agent type.')
@click.option('--stdout',
              is_flag=True,
              help='Print output to stdout')
def main(event_type, event_datetime, event_detail, event_outcome,
         event_outcome_detail, workspace, agent_name, agent_type,
         stdout, event_target):
    """The script creates provenance metadata for the package. The metadata
    contains event and, if given, also agent of the event.

    \b
    EVENT_TYPE: Type of the event.
    EVENT_DATETIME: Timestamp of the event.
    """
    run(event_type, event_datetime, event_detail, event_outcome,
        event_outcome_detail, workspace, agent_name, agent_type,
        stdout, event_target)

    return 0


def run(event_type, event_datetime, event_detail, event_outcome,
        event_outcome_detail=None, workspace="./workspace", agent_name=None,
        agent_type=None, stdout=False, event_target=None):
    """The script creates provenance metadata for the package. The metadata
    contains event and, if given, also agent of the event.
    """
    event_file = None
    directory = None

    if event_target and os.path.isdir(event_target):
        directory = os.path.normpath(event_target)
    elif event_target and os.path.isfile(event_target):
        event_file = event_target
    elif not event_target:
        directory = '.'

    if agent_name or agent_type:
        agent_identifier = str(uuid4())
        agent = create_premis_agent(agent_name,
                                    agent_type, agent_identifier)

        agent_creator = PremisCreator(workspace)
        agent_creator.add_md(agent, event_file, directory=directory)
        agent_creator.write(mdtype="PREMIS:AGENT", stdout=stdout)

        if stdout:
            print xml_helpers.utils.serialize(agent)
    else:
        agent_identifier = None

    event = create_premis_event(
        event_type,
        event_datetime,
        event_detail,
        event_outcome,
        event_outcome_detail,
        agent_identifier
    )

    creator = PremisCreator(workspace)
    creator.add_md(event, event_file, directory=directory)
    creator.write(mdtype="PREMIS:EVENT", stdout=stdout)

    if stdout:
        print xml_helpers.utils.serialize(event)


class PremisCreator(AmdCreator):
    """Subclass of AmdCreator, which generates PREMIS event
    or agent metadata.
    """

    def write(self, mdtype="PREMIS", mdtypeversion="2.3",
              section="digiprovmd", stdout=False):
        super(PremisCreator, self).write(
            mdtype=mdtype, mdtypeversion=mdtypeversion, section=section)


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
    output_filename = '%s-agent-amd.xml' % (event_type)
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
    output_filename = '%s-event-amd.xml' % event_type
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


if __name__ == '__main__':
    RETVAL = main()  # pylint: disable=no-value-for-parameter
    sys.exit(RETVAL)
