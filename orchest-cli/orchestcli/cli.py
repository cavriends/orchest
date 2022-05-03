"""The Orchest CLI.

Polling the API from your browser:
    kubectl proxy --port=8000
Then go to a URL, e.g:
http://localhost:8000/apis/orchest.io/v1alpha1/namespaces/orchest/orchestclusters/cluster-1

Example working with custom objects:
https://github.com/kubernetes-client/python/blob/v21.7.0/kubernetes/docs/CustomObjectsApi.md

"""
import collections
import typing as t
from gettext import gettext

import click
from orchestcli import cmds

# TODO: config values
NAMESPACE = "orchest"
ORCHEST_CLUSTER_NAME = "cluster-1"
APPLICATION_CMDS = ["adduser"]


class ClickCommonOptionsCmd(click.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the common commands to the beginning of the list so that
        # they are displayed first in the help menu.
        self.params: t.List[click.Option] = [
            click.Option(
                ("-n", "--namespace"),
                default=NAMESPACE,
                show_default=True,
                help="Namespace of Orchest Cluster.",
            ),
            click.Option(
                ("-c", "--cluster-name"),
                default=ORCHEST_CLUSTER_NAME,
                show_default=True,
                help="Name of Orchest Cluster.",
            ),
        ] + self.params


class ClickHelpCategories(click.Group):
    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            commands.append((subcommand, cmd))

        # allow for 3 times the default spacing
        if len(commands):
            limit = formatter.width - 6 - max(len(cmd[0]) for cmd in commands)

            categories: t.Dict[
                str, t.List[t.Tuple[str, str]]
            ] = collections.defaultdict(list)
            for subcommand, cmd in commands:
                help = cmd.get_short_help_str(limit)

                # TODO: Instead we could make it into a separate click
                # group and add both groups to the cli entrypoint group.
                if subcommand in APPLICATION_CMDS:
                    categories["Application Commands"].append((subcommand, help))
                else:
                    categories["Cluster Management Commands"].append((subcommand, help))

            if categories:
                for category, rows in categories.items():
                    with formatter.section(gettext(category)):
                        formatter.write_dl(rows)


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
    cls=ClickHelpCategories,
)
def cli():
    """The Orchest CLI to manage your Orchest Cluster on Kubernetes.

    \b
    Exit status:
        0   if OK,
        1   if Failure.

    """
    pass


@click.option(
    "--cloud",
    is_flag=True,
    default=False,
    show_default=True,
    hidden=True,
    help="Run in cloud mode after install.",
)
@click.option(
    "--fqdn",
    default=None,
    show_default=True,
    help="Fully Qualified Domain Name that Orchest listens on.",
)
@cli.command(cls=ClickCommonOptionsCmd)
def install(cloud: bool, fqdn: t.Optional[str], **common_options) -> None:
    """Install Orchest."""
    cmds.install(cloud, fqdn, **common_options)


@click.option(
    "--version",
    default=None,
    show_default=True,
    help="Version to update the Orchest Cluster to.",
)
@click.option(
    "--watch/--no-watch",
    "watch_flag",  # name for arg
    is_flag=True,
    default=True,
    show_default=True,
    help="Watch cluster status changes.",
)
@cli.command(cls=ClickCommonOptionsCmd)
def update(version: t.Optional[str], watch_flag: bool, **common_options) -> None:
    """Update Orchest.

    If `--version` is not given, then it tries to update Orchest to the
    latest version.

    \b
    Note:
        The operation fails if the Orchest Cluster would be downgraded.

    """
    cmds.update(version, watch_flag, **common_options)


@cli.command(cls=ClickCommonOptionsCmd)
@click.option(
    "--dev/--no-dev",
    is_flag=True,
    default=None,
    show_default=True,
    help="Run in development mode.",
)
@click.option(
    "--cloud/--no-cloud",
    is_flag=True,
    default=None,
    show_default=True,
    hidden=True,
    help="Run in cloud mode.",
)
@click.option(
    "--log-level",
    default=None,
    show_default=True,
    type=click.Choice(cmds.LogLevel),
    help="Log level to set on Orchest services.",
)
def patch(
    dev: t.Optional[bool],
    cloud: t.Optional[bool],
    log_level: t.Optional[cmds.LogLevel],
    **common_options,
) -> None:
    """Patch the Orchest Cluster.

    \b
    Usage:
        # Run Orchest in development mode.
        orchest patch --dev

    """
    cmds.patch(dev, cloud, log_level, **common_options)


@cli.command(cls=ClickCommonOptionsCmd)
@click.option(
    "--json",
    "json_flag",  # name for arg
    is_flag=True,
    default=False,
    show_default=False,
    help="Get output in json.",
)
def version(json_flag: bool, **common_options) -> None:
    """Get running Orchest version.

    \b
    Equivalent `kubectl` command:
        kubectl -n <namespace> get orchestclusters <cluster-name> -o jsonpath="{.spec.orchest.version}"

    """
    cmds.version(json_flag, **common_options)


@cli.command(cls=ClickCommonOptionsCmd)
@click.option(
    "--json",
    "json_flag",  # name for arg
    is_flag=True,
    default=False,
    show_default=False,
    help="Get output in json.",
)
def status(json_flag: bool, **common_options) -> None:
    """Get Orchest Cluster status.

    If invoked with `--json`, then failure to get Orchest Cluster status
    will return an empty JSON Object, i.e. `{}`.

    \b
    Equivalent `kubectl` command:
        kubectl -n <namespace> get orchestclusters <cluster-name> -o jsonpath="{.status.message}"

    """
    cmds.status(json_flag, **common_options)


@cli.command(cls=ClickCommonOptionsCmd)
@click.option(
    "--watch/--no-watch",
    "watch",  # name for arg
    is_flag=True,
    default=True,
    show_default=True,
    help="Watch status changes.",
)
def stop(watch: bool, **common_options) -> None:
    """Stop Orchest.

    All underlying Orchest deployments will scaled to zero replicas.

    \b
    Equivalent `kubectl` command:
        kubectl -n orchest patch orchestclusters cluster-1 --type='merge' -p='{"spec": {"orchest": {"pause": true}}}'
    """
    cmds.stop(watch, **common_options)


@cli.command(cls=ClickCommonOptionsCmd)
@click.option(
    "--watch/--no-watch",
    "watch",  # name for arg
    is_flag=True,
    default=True,
    show_default=True,
    help="Watch status changes.",
)
def start(watch: bool, **common_options) -> None:
    """Start Orchest.

    \b
    Equivalent `kubectl` command:
        kubectl -n orchest patch orchestclusters cluster-1 --type='merge' -p='{"spec": {"orchest": {"pause": false}}}'
    """
    cmds.start(watch, common_options)


@cli.command(cls=ClickCommonOptionsCmd)
@click.option(
    "--watch/--no-watch",
    "watch",  # name for arg
    is_flag=True,
    default=True,
    show_default=True,
    help="Watch status changes.",
)
def restart(watch: bool, **common_options) -> None:
    """Restart Orchest.

    Useful to reinitialize the Orchest application for config changes to
    take effect.

    \b
    Equivalent `kubectl` command:
        kubectl -n orchest patch orchestclusters cluster-1 --type='merge' \\
        \t-p='{"metadata": {"annotations": {"orchest.io/restart": "true"}}}'

    """
    cmds.restart(watch, **common_options)


@cli.command(cls=ClickCommonOptionsCmd)
@click.argument("username")
@click.option(
    "--is-admin",
    is_flag=True,
    default=False,
    show_default=False,
    help="Whether to make the user an admin.",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    show_default=False,
    help="Use non-interactive mode for password and token.",
)
@click.option(
    "--non-interactive-password",
    default=None,
    show_default=False,
    help="User password, provided non-interactively.",
)
@click.option(
    "--set-token",
    is_flag=True,
    default=False,
    show_default=False,
    help="Prompt asking for a machine token to identify user with.",
)
@click.option(
    "--non-interactive-token",
    default=None,
    show_default=False,
    help="Machine token to identify user with, provided non-interactively.",
)
def adduser(
    username: str,
    is_admin: bool,
    non_interactive: bool,
    non_interactive_password: t.Optional[str],
    set_token: bool,
    non_interactive_token: t.Optional[str],
    **common_options,
) -> None:
    """Add a new user to Orchest.

    \b
    Usage:
        # Adding a new user non-interactively. This can be useful for
        # automations.
        orchest adduser UserName --non-interactive --non-interactive-password=password
        \b
        # Get prompts to enter password and machine token.
        orchest adduser UserName --set-token
    """
    cmds.adduser(
        username,
        is_admin,
        non_interactive,
        non_interactive_password,
        set_token,
        non_interactive_token,
        **common_options,
    )
