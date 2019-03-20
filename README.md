# proxmox_balance

proxmox_balance is a python tool to analyze cluster distribution on a proxmox cluster.

## Install
### Clone
```bash
git clone git@github.com:lgaggini/proxmox_balance.git
```

### [Virtualenv](https://virtualenvwrapper.readthedocs.io/en/latest/command_ref.html) (strongly suggested but optional)
```bash
mkvirtualenv -a proxmox_balance proxmox_balance
```

### Requirements
```bash
pip install -r requirements.txt
```

## Configuration
Before use you have to configure proxmox connection and auth settings in `settings.py`. You can configure also
some default for thresholds. settings.samples is a settings file sample.

## Usage

```bash
usage: proxmox_balance.py [-h] [-k {cluster,qty,percentage,node}]
                          [-p PERCENTAGE] [-t THRESHOLD] [-n NODE]
                          [-l {debug,info,warning,error,critical}]

proxmox_balance, analyze cluster distribution on nodes

optional arguments:
  -h, --help            show this help message and exit
  -k {cluster,qty,percentage,node}, --key {cluster,qty,percentage,node}
                        sorg key (default vm name)
  -p PERCENTAGE, --percentage PERCENTAGE
                        percentage threshold
  -t THRESHOLD, --threshold THRESHOLD
                        static threshold
  -n NODE, --node NODE  filter by node
  -l {debug,info,warning,error,critical}, --log-level {debug,info,warning,error,critical}
                        log level (default info)
```
