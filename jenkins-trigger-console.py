#!/usr/bin/env python
"""jenkins-trigger-console.py

Usage:
    jenkins-trigger-console.py --job <jobname> [--url <url>] [--sleep <sleep_time>] [--encoding <type>] [--parameters <data>] [--wait-timer <time>] [--debug] [--user <username>] [--pass <password>]
    jenkins-trigger-console.py -h

Examples:
    jenkins-trigger-console.py  --job deploy_my_app -e text -u https://jenkins.example.com:8080 -p param1=1,param2=develop

Options:
  -j, --job <jobname>               Job name.
  -u, --url <url>                   Jenkins URL [default: http://localhost:8080]
  -s, --sleep <sleep_time>          Sleep time between polling requests [default: 2]
  -w, --wait-timer <time>           Wait time in queue [default: 100]
  -e, --encoding <type>             Encoding type supports text or html [default: html]
  --user <username>                 Username for the remote Jenkins user
  --pass <password>                 Password or API key for the remote Jenkins user
  -p, --parameters <data>           Comma separated job parameters i.e. a=1,b=2
  -d, --debug                       Print debug info
  -h, --help                        Show this screen and exit.
"""

import requests
from docopt import docopt
from time import sleep
import os


class Trigger():
    def __init__(self, arguments):
        self.arguments = arguments
        self.debug = arguments['--debug']
        if self.debug:
            print "argument = ", arguments
        self.url = arguments['--url']
        self.job = arguments['--job']
        self.timer = int(arguments['--wait-timer'])
        self.sleep = int(arguments['--sleep'])
        self.encoding = arguments['--encoding']
        self.debug = arguments['--debug']
        username = os.environ.get('REMOTE_JENKINS_USER') or os.arguments['--user']
        password = os.environ.get('REMOTE_JENKINS_PASS') or arguments['--pass']
        self.crumb = None
        self.auth = None
        if username and password:
            self.auth = (username, password)
            self.crumb = self.get_crumb()
        if self.encoding.lower() in ["html", "text"]:
            self.encoding = self.encoding.title()
        else:
            print " '%s' is not a valid encoding only support 'text', 'html'" % self.encoding
            exit(1)
        if arguments['--parameters']:
            try:
                self.parameters = dict(u.split("=") for u in arguments['--parameters'].split(","))
            except ValueError:
                print "Your parameters should be in key=value format separated by ; for multi value i.e. x=1,b=2"
                exit(1)
        else:
            self.parameters = False


    def get_crumb(self):
        # Get Jenkins crumb
        r = requests.get(self.url + '/crumbIssuer/api/json',
                         auth=self.auth
        )
        r.raise_for_status()
        crumb_data = r.json()
        return {
                crumb_data['crumbRequestField']: crumb_data['crumb']
        }


    def trigger_build(self):
        # Do a build request
        if self.parameters:
            build_url = self.url + "/job/" + self.job + "/buildWithParameters"
            print "Triggering a build via post @ ", build_url
            if self.auth:
                build_request = requests.post(build_url,
                        data=self.parameters,
                        auth=self.auth,
                        headers=self.crumb
                        )
            else:
                build_request = requests.post(build_url, data=self.parameters)

        else:
            build_url = self.url + "/job/" + self.job + "/build"
            print "Triggering a build via get @ ", build_url
            if self.auth:
                build_request = requests.get(build_url,
                        auth=(self.username,self.password),
                        headers={crumb_data['key']: crumb_data['value']}
                        )
            else:
                build_request = requests.get(build_url),


        if build_request.status_code == 201:
            queue_url =  build_request.headers['location'] +  "/api/json"
            print "Build is queued @ ", queue_url
        else:
            print "Your build somehow failed"
            print build_request.status_code
            print build_request.text
            exit(1)
        return queue_url

    def waiting_for_job_to_start(self, queue_url):
        # Poll till we get job number
        print ""
        print "Starting polling for our job to start"
        timer = self.timer

        waiting_for_job = True
        while waiting_for_job:
            queue_request = requests.get(queue_url)
            if queue_request.json().get("why") != None:
                print " . Waiting for job to start because :", queue_request.json().get("why")
                timer -= 1
                sleep(self.sleep)
            else:
                waiting_for_job = False
                job_number = queue_request.json().get("executable").get("number")
                print " Job is being build number: ", job_number

            if timer == 0:
                print " time out waiting for job to start"
                exit(1)
        # Return the job numner of the working
        return job_number


    def console_output(self, job_number):
        # Get job console till job stops
        job_url = self.url + "/job/" + self.job + "/" + str(job_number) + "/logText/progressive" + self.encoding
        print " Getting Console output @ ", job_url
        start_at = 0
        stream_open = True
        check_job_status = 0

        console_requests = requests.session()
        while stream_open:
            if self.auth:
                console_response = console_requests.post(job_url, data={'start': start_at }, auth=self.auth, headers=self.crumb)
            else:
                console_response = console_requests.post(job_url, data={'start': start_at })
            content_length = int(console_response.headers.get("Content-Length",-1))

            if console_response.status_code != 200:
                print " Oppps we have an issue ... "
                print console_response.content
                print console_response.headers
                exit(1)

            if content_length == 0:
                sleep(self.sleep)
                check_job_status +=1
            else:
                check_job_status = 0
                # Print to screen console
                print console_response.content
                sleep(self.sleep)
                start_at = int(console_response.headers.get("X-Text-Size"))

            # No content for a while lets check if job is still running
            if check_job_status > 1:
                job_status_url = self.url + "/job/" + self.job + "/" + str(job_number) + "/api/json"
                job_requests = requests.get(job_status_url)
                job_bulding= job_requests.json().get("building")
                if not job_bulding:
                    # We are done
                    print "stream ended"
                    stream_open = False
                else:
                    # Job is still running
                    check_job_status = 0

    def main(self):
        queue_url = self.trigger_build()
        job_number = self.waiting_for_job_to_start(queue_url)
        self.console_output(job_number)

if __name__ == '__main__':
    arguments = docopt(__doc__)
    myrigger = Trigger(arguments)
    myrigger.main()
