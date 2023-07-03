#!/usr/bin/python
#
# core Nagios classes.
#

class Nagios:
    '''This class represents the current state of a Nagios installation, as read
    from the status file that Nagios maintains.

    '''
    def __init__(self, statusfile=None):
        '''Create a new Nagios state store.  One argument, statusfile, is used to
        indicate where the status file is.  This object is intended to be read-only
        once it has been created.

        '''
        self.info = Info({})
        self.program = Program({})
        self.hosts = {}
        self.services = {}
        self.comments = {}
        self.downtimes = {}
        if statusfile is not None:
            self._update(statusfile)

    def _update(self, statusfile):
        '''Read the status file from Nagios and parse it.  Responsible for building
        our internal representation of the tree.

        '''
        # Generator to get the next status stanza.
        def next_stanza(f):
            cur = None
            for line in f:
                line = line.strip()
                if line.endswith('{'):
                    if cur is not None:
                        yield cur
                    cur = {'type': line.split(' ', 1)[0]}
                elif '=' in line:
                    key, val = line.split('=', 1)
                    if key == "performance_data":
                        # performance_data is special
                        performance_data = {}
                        split = val.split(' ')
                        for dat in split:
                            chunks = dat.split(';', 1)
                            if chunks and len(chunks) > 0 and '=' in chunks[0]:
                                (c_key, c_val) = chunks[0].split('=', 1)
                                # convert to int or float if possible
                                try:
                                    n_val = float(c_val)
                                    if (n_val == int(n_val)):
                                        n_val = int(n_val)
                                except ValueError:
                                    n_val = c_val
                                performance_data[c_key] = n_val
                        val = performance_data
                    cur[key] = val
                elif "#" in line:
                    if not line.find("NAGIOS STATE RETENTION FILE"):
                        raise ValueError("You appear to have used the state retention file instead of the status file. Please change your arguments and try again.")
            if cur is not None:
                yield cur

        f = open(statusfile, 'r')
        for obj in next_stanza(f):
            host = obj['host_name'] if 'host_name' in obj else None
            service = obj['service_description'] if 'service_description' in obj else None

            if obj['type'] == 'hoststatus':
                self.hosts[host] = Host(obj)
            elif obj['type'] == 'servicestatus':
                if host not in self.services:
                    self.services[host] = {}
                self.services[host][service] = Service(obj)
            elif obj['type'].endswith('comment'):
                self.comments[int(obj['comment_id'])] = Comment(obj)
            elif obj['type'].endswith('downtime'):
                self.downtimes[int(obj['downtime_id'])] = Downtime(obj)
            elif obj['type'] == 'info':
                self.info = Info(obj)
            elif obj['type'] == 'programstatus':
                self.program = Program(obj)
        f.close()

        for host in self.services:
            for s in self.services[host].itervalues():
                self.host_or_service(host).attach_service(s)
        for c in self.comments.itervalues():
            tmp = self.host_or_service(c.host, c.service)
            if (tmp is None):
                # FIXME: throw something?
                pass
            else:
                tmp.attach_comment(c)
        for d in self.downtimes.itervalues():
            self.host_or_service(d.host, d.service).attach_downtime(d)

    def host_or_service(self, host, service=None):
        '''Return a Host or Service object for the given host/service combo.
        Note that Service may be None, in which case we return a Host.

        '''
        if service is not None:
            try:
                service = service.encode('utf-8')
            except:
                pass
        if host not in self.hosts:
            return None
        if service is None:  # Only a Host if they really want it.
            return self.hosts[host]
        if host not in self.services or service not in self.services[host]:
            return None
        return self.services[host][service]

    def for_json(self):
        '''Given a Nagios state object, return a pruned down dict that is
        ready to be serialized to JSON.

        '''
        out = {}
        for host in self.hosts:
            out[host] = self.hosts[host].for_json()
        return out


class NagiosObject:
    '''A base class that does a little fancy parsing.  That's it.

    '''
    def __init__(self, obj):
        '''Builder for the base.'''
        for key in obj:
            self.__dict__[key] = obj[key]
        self.host = getattr(self, 'host_name', None)
        self.service = getattr(self, 'service_description', None)
        self.essential_keys = []

    def for_json(self):
        '''Return a dict of ourselves that is ready to be serialized out
        to JSON.  This only returns the data that we think is essential for
        any UI to show.

        '''
        obj = {}
        for key in self.essential_keys:
            obj[key] = getattr(self, key, None)
        return obj


class Info(NagiosObject):
    def __init__(self, obj):
        NagiosObject.__init__(self, obj)
        self.essential_keys = ['created', 'version', 'last_update_check',
           'update_available', 'last_version', 'new_version']


class Program(NagiosObject):
    def __init__(self, obj):
        NagiosObject.__init__(self, obj)
        self.essential_keys = [
            'modified_host_attributes',
            'modified_service_attributes',
            'nagios_pid',
            'daemon_mode',
            'program_start',
            'last_log_rotation',
            'enable_notifications',
            'active_service_checks_enabled',
            'passive_service_checks_enabled',
            'active_host_checks_enabled',
            'passive_host_checks_enabled',
            'enable_event_handlers',
            'obsess_over_services',
            'obsess_over_hosts',
            'check_service_freshness',
            'check_host_freshness',
            'enable_flap_detection',
            'process_performance_data',
            'global_host_event_handle',
            'global_service_event_handle',
            'next_comment_id',
            'next_downtime_id',
            'next_event_id',
            'next_problem_id',
            'next_notification_id',
            'active_scheduled_host_check_stats',
            'active_ondemand_host_check_stats',
            'passive_host_check_stats',
            'active_scheduled_service_check_stats',
            'active_ondemand_service_check_stats',
            'passive_service_check_stats',
            'cached_host_check_stats',
            'cached_service_check_stats',
            'external_command_stats',
            'parallel_host_check_stats',
            'serial_host_check_stats'
        ]


class HostOrService(NagiosObject):
    '''Represent a single host or service.

    '''
    def __init__(self, obj):
        '''Custom build a HostOrService object.'''
        NagiosObject.__init__(self, obj)
        self.downtimes = {}
        self.comments = {}
        self.essential_keys = ['current_state', 'plugin_output',
            'notifications_enabled', 'last_check', 'last_notification',
            'active_checks_enabled', 'problem_has_been_acknowledged',
            'last_hard_state', 'scheduled_downtime_depth', 'performance_data',
            'last_state_change', 'current_attempt', 'max_attempts']

    def attach_downtime(self, dt):
        '''Given a Downtime object, store a record to it for lookup later.'''
        self.downtimes[dt.downtime_id] = dt

    def attach_comment(self, cmt):
        '''Given a Comment object, store a record to it for lookup later.'''
        self.comments[cmt.comment_id] = cmt



class Host(HostOrService):
    '''Represent a single host.

    '''
    def __init__(self, obj):
        '''Custom build a Host object.'''
        HostOrService.__init__(self, obj)
        self.services = {}

    def attach_service(self, svc):
        '''Attach a Service to this Host.'''
        self.services[svc.service] = svc

    def for_json(self):
        '''Represent ourselves and also get attached data.'''
        obj = NagiosObject.for_json(self)
        for key in ('services', 'comments', 'downtimes'):
            obj[key] = {}
            for idx in self.__dict__[key]:
                obj[key][idx] = self.__dict__[key][idx].for_json()
        return obj


class Service(HostOrService):
    '''Represent a single service.

    '''
    def for_json(self):
        '''Represent ourselves and also get attached data.'''
        obj = NagiosObject.for_json(self)
        for key in ('comments', 'downtimes'):
            obj[key] = {}
            for idx in self.__dict__[key]:
                obj[key][idx] = self.__dict__[key][idx].for_json()
        return obj


class Comment(NagiosObject):
    '''Represent a single comment.

    '''
    def __init__(self, obj):
        '''Custom build a Comment object.'''
        NagiosObject.__init__(self, obj)
        self.essential_keys = ['comment_id', 'entry_type', 'source',
            'persistent', 'entry_time', 'expires', 'expire_time', 'author',
            'comment_data']
        self.comment_id = int(self.comment_id)


class Downtime(NagiosObject):
    '''Represent a single downtime event.

    '''
    def __init__(self, obj):
        '''Custom build a Downtime object.'''
        NagiosObject.__init__(self, obj)
        self.essential_keys = ['downtime_id', 'entry_time', 'start_time',
            'end_time', 'triggered_by', 'fixed', 'duration', 'author',
            'comment']
        self.downtime_id = int(self.downtime_id)
