## Caffeine Monitor

#### Tracks the caffeine level in the user's body

##### Disclaimer
*This code is for entertainment use only.*

##### Prerequisites
A linux system, with Python 3.7 or higher installed.  
Run `pip install -r requirements.txt` to install other prerequisites.  
So far, the code has been tested only on a machine running Fedora 31 and Python 3.7.  

##### Overview
This script uses a simple 
[exponential decay function](https://github.com/jazcap53/caffeine_monitor/blob/2d2dd2927cc8e5b97806ce00d0a0c1c0ccc6c0eb/src/caffeine_monitor.py#L79-L80) 
to calculate the approximate level of
caffeine in the user's body. It assumes a half-life of 360 minutes for caffeine.  

When called with no arguments, the script displays its estimate of that level.  
When called with one argument, it adds that number of mg of caffeine to the level.  
If you drank a cup of coffee an hour ago, but forgot to "tell" the script, call it with
two arguments. The second argument is how long ago, in minutes, you had the coffee.

##### Details
##### Production
Caffeine Monitor maintains two files, whose names can be read from `caffeine.ini`. The user
must maintain an environment variable, `CAFF_ENV`, which is set to `prod` except while
working on the code.

The file `src/caffeine.json` holds the time and level of the most recent reading. It is updated
whenever the user interacts with the script.  

The file `src/caffeine.log` is updated whenever the user modifies the level.

##### Test
To set up a test environment, simply export `CAFF_ENV=test`.  Then call the script
with or without arguments, but with a `-t` switch appended. A file `test/caff_test.json`
will be created. If a first argument is given, a `test/caff_test.log` file is created. 

##### Convenience symlink
I recommend creating a symlink in the project root directory to the 
executable `src/caffeine_monitor.py`, using e.g. `ln -s src/caffeine_monitor.py caff`.
This allows the script to be run as `./caff`.

##### Non-interference
The script is set up so that, if no `-t` c.l.a. is given, it will only access the 
production data. Conversely, if the `-t` switch *is* present, the script will only
access test data.
