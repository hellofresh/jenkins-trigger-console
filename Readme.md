Jenkins tirgger console
========================

Is a simple python script that triggers jobs on remote Jenkins and follows the console output.

## Usage

```
Usage:
    jenkins-trigger-console.py --job <jobname> [--url <url>] [--sleep <sleep_time>] [--encoding <type>] [--parameters <data>] [--wait-timer <time>] [--debug]
    jenkins-trigger-console.py -h

Examples:
    jenkins-trigger-console.py  --job deploy_my_app -e text -u https://jenkins.example.com:8080 -p param1=1,param2=develop

Options:
  -j, --job <jobname>               Job name.
  -u, --url <url>                   Jenkins URL [default: http://localhost:8080]
  -s, --sleep <sleep_time>          Sleep time between polling requests [default: 2]
  -w, --wait-timer <time>           Wait time in queue [default: 100]
  -e, --encoding <type>             Encoding type supports text or html [default: html]
  -p, --parameters <data>           Comma separated job parameters i.e. a=1,b=2
  -d, --debug                       Print debug info
  -h, --help                        Show this screen and exit.
```

## License
MIT

### Contributors
* [Adham Helal](https://github.com/ahelal)