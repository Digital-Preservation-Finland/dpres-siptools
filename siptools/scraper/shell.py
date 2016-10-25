"""General interface for building a file validator plugin. """
import subprocess


class Shell(object):

    """Docstring for ShellTarget. """

    def __init__(self, command, output_file=subprocess.PIPE):
        """Initialize instance.

        :command: Command to execute as list
        """
        self.command = command

        self._stdout = None
        self._stderr = None
        self._returncode = None
        self.output_file = output_file

    @property
    def returncode(self):
        """Returncode from the command

        :returns: Returncode

        """
        return self.run()["returncode"]

    @property
    def stderr(self):
        """Standard error output from the command

        :returns: Stdout as string

        """
        return self.run()["stderr"]

    @property
    def stdout(self):
        """Command standard error output.

        :returns: Stderr as string

        """
        return self.run()["stdout"]

    def run(self):
        """Run the command and store results to class attributes for caching.

        :returns: Returncode, stdout, stderr as dictionary

        """
        if self._returncode is None:
            proc = subprocess.Popen(
                self.command, stdout=self.output_file,
                stderr=subprocess.PIPE, shell=False)
            (self._stdout, self._stderr) = proc.communicate()

            self._returncode = proc.returncode

        return {
            'returncode': self._returncode,
            'stderr': self._stderr,
            'stdout': self._stdout
            }
