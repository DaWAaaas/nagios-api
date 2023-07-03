# Nagios API
nagios-api - presents a REST-like JSON interface to Nagios.

## Description
This program provides a simple REST-like interface to Nagios. Run this
on your Nagios host and then sit back and enjoy a much easier, more
straightforward way to accomplish things with Nagios. You can use the
bundled nagios-cli, but you may find it easier to write your own system
for interfacing with the API.

## Synopsis
`nagios-api [OPTIONS]`

## Dependencies
Dependencies include:

- diesel
- greenlet
- python-openssl

These should be available via pip/easy_install.

## Usage
Usage is pretty easy:

```
nagios-api -p 8080 -c /var/lib/nagios3/rw/nagios.cmd\
-s /var/cache/nagios3/status.dat -l /var/log/nagios3/nagios.log
```

You must at least provide the status file options. If you don't provide
the other options, then we will disable that functionality and error to
clients who request it.

## Using the API
The server speaks [JSON](http://www.json.org/). You can either GET data from it or POST data to
it and take an action. It's pretty straightforward, here's an idea of
what you can do from the command line:

```
curl http://localhost:8080/state
```

That calls the `state` method and returns the JSON result.

```
curl -d '{"host": "web01", "duration": 600}' -H 'Content-Type: application/json' http://localhost:8080/schedule_downtime
```

This POSTs the given JSON object to the `schedule_downtime` method. You
will note that all objects returned follow a predictable format:

```
{"content": <object>, "result": <bool>}
```

The `result` field is always `true` or `false`, allowing you to
determine at a glance if the command succeeded. The `content` field may
be any valid JavaScript object: an int, string, null, bool, hash, list,
etc etc. What is returned depends on the method being called.

## Using `nagios-cli`
Once your API server is up and running you can access it through the
included nagios-cli script. The script now has some decent built-in help
so you should be able to get all you need:

```
nagios-cli -h
```

The original raw JSON mode is still supported by passing the --raw
option.

## Options
Below are the options taken on the CLI.

```
-p, --port=PORT
```

Listen on port 'PORT' for HTTP requests.

```
-b, --bind=ADDR
```

Bind to ADDR for HTTP requests (defaults to all interfaces).

```
-c, --command-file=FILE
```

Use 'FILE' to write commands to Nagios. This is where external
commands are sent. If your Nagios installation does not allow
external commands, do not set this option.

```
-d, --config-directory=PATH
```

The directory in which Nagios will look for object files and import
hosts into its internal database for monitoring.

```
-s, --status-file=FILE
```

Set 'FILE' to the status file where Nagios stores its status
information. This is where we learn about the state of the world and
is the only required parameter.

```
-l, --log-file=FILE
```

Point 'FILE' to the location of Nagios's log file if you want to
allow people to subscribe to it.

```
-o, --allow-origin=ORIGIN
```

Modern web browsers implement the Cross-Origin Resource Sharing
specification from W3C. This spec allows you to host your
JavaScript/HTML on one host and have it access an endpoint on a
different service. This requires setting a header on the endpoint,
which this option allows you to do.

You can simply set this header to ``` and not worry about it
if you want to allow all access. For more information see the
[CORS specification](http://www.w3.org/TR/cors/).

```
-q, --quiet
```

If present, we will only print warning/critical messages. Useful if
you are running this in the background.

## API
This program currently supports only a subset of the Nagios API. More
is being added as it is needed. If you need something that isn't here,
please consider submitting a patch!

This section is organized into methods and sorted alphabetically. Each
method is specified as a URL and may include an integer component on the
path. Most data is passed as JSON objects in the body of a POST.

### `acknowledge_problem`
This method allows you to acknowledge a given problem on a host or service.

```
{
  "host": "string",
  "service": "string",
  "comment": "string",
  "sticky": true,
  "notify": true,
  "persistent: true,
  "expire": 0,
  "author": "string"
}
```

#### Fields
`host` = `STRING [required]`

Which host to act on.

`service` = `STRING [optional]`

If specified, act on this service.

`comment` = `STRING [required]`

This is required and should contain some sort of message that explains why
this alert is being acknowledged.

`sticky` = `BOOL [optional]`

default TRUE. When true, this acknowledgement stays until the
host enters an OK state. If false, the acknowledgement clears on ANY state
change.

`notify` = `BOOL [optional]`

default TRUE. Whether or not to send a notification that this
problem has been acknowledged.

`persistent` = `BOOL [optional]`

default FALSE. If this is enabled, the comment given will stay
on the host or service. By default, when an acknowledgement expires, the
comment associated with it is deleted.

`expire` = `INTEGER [optional]`

default 0.  If set, it will (given icinga >= 1.6) expire the
acknowledgement at the given timestamp. Seconds since the UNIX epoch. Defaults
to 0 (off).

`author` = `STRING [optional]`

The name of the author. This is useful in UIs if you want
to disambiguate who is doing what.

### `add_comment`
For a given host and/or service, add a comment. This is free-form text that can
include whatever you want and is visible in the Nagios UI and API output.

```
{
  "host": "string",
  "service": "string",
  "comment": "string",
  "persistent: true,
  "author": "string"
}
```

#### Fields
`host` = `STRING [required]`

Which host to act on.

`service` = `STRING [optional]`

If specified, act on this service.

`comment` = `STRING [required]`

This is required and should contain the text of the comment you want to
add to this host or service.

`persistent` = `BOOL [optional]`

Optional, default FALSE. If this is enabled, the comment given will stay
on the host or service until deleted manually. By default, they only stay
until Nagios is restarted.

`author` = `STRING [optional]`

The name of the author. This is useful in UIs if you want
to disambiguate who is doing what.

### `cancel_downtime`
Very simply, this immediately lifts a downtime that is currently in
effect on a host or service. If you know the `downtime_id`, you can
specify that as a URL argument like this:

```
curl -d "{}" http://localhost:8080/cancel_downtime/15
```

That would cancel the downtime with `downtime_id` of 15. Most of the
time you will probably not have this information and so we allow you to
cancel by host/service as well.

```
{
  "host": "string",
  "service": "string",
  "services_too": true
}
```

#### Fields
`host` = `STRING [required]`

Which host to cancel downtime from.  This must be specified if you
are not using the `downtime_id` directly.

`service` = `STRING [optional]`

If specified, cancel any downtimes on this service.

`services_too` = `BOOL [optional]`

If true and you have not specified a `service` in
specific, then we will cancel all downtimes on this host and all of
the services it has.

### `disable_notifications`
This disables alert notifications on a host or service. (As an operational
note, you might want to schedule downtime instead. Disabling notifications
has a habit of leaving things off and people forgetting about it.)

```
{
  "host": "string",
  "service": "string"
}
```

#### Fields
`host` = `STRING [required]`

Which host to act on.

`service` = `STRING [optional]`

If specified, act on this service.

### `delete_comment`
Deletes comments from a host or service. Can be used to delete all comments or
just a particular comment.

```
{
  "host": "string",
  "service": "string",
  "comment_id": 1234
}
```

#### Fields
`host` = `STRING [required]`

Which host to act on.

`service` = `STRING [optional]`

If specified, act on this service.

`comment_id` = `INTEGER [required]`

The ID of the comment you wish to delete. You may set this to `-1` to delete
all comments on the given host or service.

### `enable_notifications`
This enables alert notifications on a host or service.

```
{
  "host": "string",
  "service": "string"
}
```

#### Fields
`host` = `STRING [required]`

Which host to act on.

`service` = `STRING [optional]`

If specified, act on this service.

### `log`
Simply returns the most recent 1000 items in the Nagios event log. These
are currently unparsed. There is a plan to parse this in the future and
return event objects.

### `status`
Simply returns a JSON that contains nagios status objects.

### `restart_nagios`
Restarts the nagios service.

### `update_host`
This method will create/update a nagios configuration file that contains devices.

```
{
  "file_name": "string",
  "text": "string"
}
```

#### Fields
`file_name` = `STRING [required]`

File name for the configuration.

`text` = `STRING [required]`

Content of the configuration file.

### `objects`
Returns a dict with the key being hostnames and the values being a list
of services defined for that host. Use this method to get the contents
of the world -- i.e., all hosts and services.

### `remove_acknowledgement`
This method cancels an acknowledgement on a host or service.

```
{
  "host": "string",
  "service": "string"
}
```

#### Fields
`host` = `STRING [required]`

Which host to act on.

`service` = `STRING [optional]`

If specified, act on this service.

### `schedule_check`
This API lets you schedule a check for a host or service. This also allows
you to force a check.

```
{
  "host": "string",
  "service": "string",
  "check_time": 1234,
  "forced: true,
  "output": "string"
}
```

#### Fields
`host` = `STRING [required]`

The host to schedule a check for. Required.

`service` = `STRING [optional]`

If present, we'll schedule a check on this service at the given
time.

`all_services` = `BOOL [optional]`

If present, we'll schedule a check on again all services at the given
time.

`check_time` = `INTEGER [optional]`

Optional, defaults to now. You can specify what time you want the check
to be run at.

`forced` = `BOOL [optional]`

Optional, defaults to FALSE. When true, then you force Nagios to run the
check at the given time. By default, Nagios will only run the check if it
meets the standard eligibility criteria.

`output` = `STRING [required]`

The plugin output to be displayed in the UI and stored.  This is a
single line of text, normally returned by checkers.

### `schedule_downtime`
This general purpose method is used for creating fixed length downtimes.
This method can be used on hosts and services. You are allowed to
specify the author and comment to go with the downtime, too. The JSON
parameters are:

```
{
  "host": "string",
  "duration": 1234,
  "service": "string",
  "services_too": true,
  "author": "string",
  "comment": "string"
}
```

#### Fields
`host` = `STRING [required]`

Which host to schedule a downtime for.  This must be specified.

`duration` = `INTEGER [required]`

How many seconds this downtime will last for. They begin immediately
and continue for `duration` seconds before ending.

`service` = `STRING [optional]`

If specified, we will schedule a downtime for this service
on the above host. If not specified, then the downtime will be
scheduled for the host itself.

`services_too` = `BOOL [optional]`

If true and you have not specified a `service` in
specific, then we will schedule a downtime for the host and all of
the services on that host. Potentially many downtimes are scheduled.

`author` = `STRING [optional]`

The name of the author. This is useful in UIs if you want
to disambiguate who is doing what.

`comment` = `STRING [optional]`

As above, useful in the UI.

The result of this method is a text string that indicates whether or
not the downtimes have been scheduled or if a different error occurred.
We do not have the ability to get the `downtime_id` that is generated,
unfortunately, as that would require waiting for Nagios to regenerate
the status file.

### `schedule_hostgroup_downtime`
This method is used for creating fixed length downtimes on all the hosts
belonging to a hostgroup. You are allowed to specify the author and comment
to go with the downtime, too. The JSON parameters are:

```
{
  "hostgroup": "string",
  "duration": 1234,
  "services_too": true,
  "author": "string",
  "comment": "string"
}
```

#### Fields
`hostgroup` = `STRING [required]`

Which hostgroup to schedule a downtime for. This must be specified.

`duration` = `INTEGER [required]`

How many seconds this downtime will last for. They begin immediately
and continue for `duration` seconds before ending.

`services_too` = `BOOL [optional]`

If true, then we will schedule a downtime for all the hosts in
the hostgroup and all of the services on those hosts.
Potentially many downtimes are scheduled.

`author` = `STRING [optional]`

The name of the author. This is useful in UIs if you want
to disambiguate who is doing what.

`comment` = `STRING [optional]`

As above, useful in the UI.

The result of this method is a text string that indicates whether or
not the downtimes have been scheduled or if a different error occurred.
We do not have the ability to get the `downtime_id` that is generated,
unfortunately, as that would require waiting for Nagios to regenerate
the status file.

### `state`
This method takes no parameters. It returns a large JSON object
containing all of the active state from Nagios. Included are all hosts,
services, downtimes, comments, and other things that may be in the
global state object.

### `submit_result`
If you are using passive service checks or you just want to submit a
result for a check, you can use this method to submit your result to
Nagios.

```
{
  "host": "string",
  "service": "string",
  "status": 1234,
  "output": "string"
}
```

#### Fields
`host` = `STRING [required]`

The host to submit a result for.  This is required.

`service` = `STRING [optional]`

If specified, we will submit a result for this service on
the above host. If not specified, then the result will be submitted
for the host itself.

`status` = `INTEGER [required]`

The status code to set this host/service check to. If you are
updating a host's status: 0 = OK, 1 = DOWN, 2 = UNREACHABLE. For
service checks, 0 = OK, 1 = WARNING, 2 = CRITICAL, 3 = UNKNOWN.

`output` = `STRING [required]`

The plugin output to be displayed in the UI and stored.  This is a
single line of text, normally returned by checkers.

The response indicates if we successfully wrote the command to the log.

## Docker
A Docker container is available for convenience. It needs to be run on
the same server as the nagios installation.

First determine the location of the `status.dat`, `nagios.log`, and
`nagios.cmd` files. Map these files into the Docker container. The
container can be started using the following command:

```
docker run -v /var/lib/nagios3/rw/nagios.cmd:/opt/nagios.cmd \
-v /var/cache/nagios3/status.dat:/opt/status.dat \
-v /var/log/nagios3/nagios.log:/opt/nagios.log \
-p 2337:8080 inventid/nagios-python-api
```

In the above case, the API will be exposed on port 2337.

## Author
Written by Mark Smith <mark@qq.is> while under the employ of Bump
Technologies, Inc.

## Copying
See the `LICENSE` file for licensing information.
