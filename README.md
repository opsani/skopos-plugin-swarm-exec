# skopos-plugin-swarm-exec

[![Join the chat at https://gitter.im/datagridsys/skopos](https://badges.gitter.im/datagridsys/skopos.svg)](https://gitter.im/datagridsys/skopos?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

A tool for executing commands in service containers deployed on Docker Swarm, as well as
a Skopos plugin for doing the same with the
[Skopos Continuous Deployment System](http://datagridsys.com).

## Background

Docker Swarm does not yet provide a way to execute commands inside a service
task from the manager node (CLI or API). This project provides an easy-to-use
mechanism for doing just that: executing a command in the container of a service task.

Think of it as a `docker service exec` that applies to a specific task of a service.

While this project is intended for use with the [Skopos Continuous Deployment System](http://datagridsys.com),
it can be used as a standalone tool to provide the same capability.

The need for this project is expected to go away when the
[Support for executing into a task #1895](https://github.com/docker/swarmkit/issues/1895)
issue is resolved in the Docker Swarm project and the same capability becomes available
directly in the Docker Swarm API and command-line client.

## Standalone Use

On the swarm manager node, run the following command:

```
docker run -v /var/run/docker.sock:/var/run/docker.sock
    datagridsys/skopos-plugin-swarm-exec \
    task-exec <taskID> <command> [<arguments>...]
```

where:

* `<taskID>` is the task ID of the task in which you want to execute a command (see task IDs with `docker service ps <service_name>`)
* `<command>` command to execute (e.g. `curl`)
* `<arguments>...` zero or more arguments to pass to the command (e.g., `http://example.com/file`)

>Note: it is possible to use the `swarm-exec` script directly, if python3 and
the docker Python SDK are installed, and the `lib` directory is included in the
Python module path. The container packaging is easier to use in most cases.


## Use With Skopos

### Setup

Copy the `plugin` directory to the host on which you run Skopos, e.g., into `~/skopos/`.
Start Skopos using the following command, on the Swarm manager node:

```
docker run -d -p 8090:80 --restart=unless-stopped --name skopos \
    -v ~/skopos/plugin:/skopos/user/bin          \
    -v /var/run/docker.sock:/var/run/docker.sock \
    datagridsys/skopos
```

Note that this will map the `plugin` directory into the Skopos container, providing
the `swarm-exec` plugin as a user-defined plugin in Skopos.

>Alternate method: re-package Skopos into a new container, starting from
the original `datagridsys/skopos` container and placing the `swarm-exec` file
directly into the `/skopos/plugins/` directory. There is no need to use the `lib`
directory, as Skopos already has the required libraries. This method eliminates the
need to use host directory mapping and may be more appropriate for production clusters.

### Model Steps

To add command execution into each instance of the newly deployed/upgraded
component, add the `lifecycle` section to the component's model section, with
one or more `call` sub-sections:

```
...
components:
  mycomponent:
    image: myrepo/myimage:1.2.3
    ...
    lifecycle:
      quality_probe:
        steps:
          - call:
              label: "execute a command" # text to show in plan view
              plugin: swarm-exec
              action: inst_exec
              arguments:
                selector: new 		    # required, don't change
                command: "sleep 3"      # command to execute, single string
...
```

For a fully functioning example app, see the [example](example/) directory. Feel
free to modify the command in the `back` component and experiment with various
commands and arguments:

* `true` - should succeed
* `false` - should fail (exit code 1)
* `foobarnone` - should fail as a non-existing command (exit code 126)
* `sleep 5` - should succeed, with a visible 5 second delay during the exec step
* `sleep 60` - should fail, as the exec timeout is set to 30 seconds

To load and run a deployment of the example app, use the following command
(assuming Skopos is on port 8090 and you are running on the same host):

`sks-ctl --bind localhost:8090 run --replace-all --env env.yaml model.yaml`

>Once loaded with the above command, it is possible to experiment by simply
changing the model using the built-in YAML editor.


### Supported Actions and Arguments

The **swarm-exec** plugin supports only one action, `inst_exec` and the following arguments for it:

* `command` - (required) command to execute, string
* `timeout` - (optional) how long to wait for command to complete, in seconds. Default: 300 seconds (5 minutes)
* `image` - (optional) alternate container image to use for invoking the container command. Default: `datagridsys/skopos-plugin-swarm-exec:latest`

## Limitations

* requires Docker Swarm, 17.03 or later, and must execute on a swarm manager node
* commands must be strings (lists don't work)
* only the exit code is returned, currently there is no way to see the output from the command

## Tips

1. To verify the plugin is working, try using `'true'` and `'false'` as commands (make sure those are in quotes to avoid parsing them as booleans)
1. If the exit code is `126`, this usually means the command's executable was not found.

## How It Works (Internals)

Starting from a task ID and a command to execute, here are the steps that are taken:

1. Obtain the node ID on which the target task is running, as well as the container ID
of the task on that node
1. Create a temporary service, using the same container image, and a scheduling constraint
that places the task of the temporary service on the same node where the target task is
1. Execute the equivalent of a `docker exec` command using the node-local Docker engine API
1. Upon completion of the command, terminate the temporary service, propagating the exit code of the executed command
1. Upon termination of the temporary service, extract the exit code and return it

## License

This is an open source project. See the [LICENSE](LICENSE) file.

## Contributing

If you want to propose an improvement, pull requests are always welcome!

You can reach the maintainers on [Gitter](https://gitter.im/datagridsys/skopos).