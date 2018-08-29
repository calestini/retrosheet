# retrosheet

[![Build Status](https://travis-ci.org/calestini/retrosheet.svg?branch=master)](https://travis-ci.org/calestini/retrosheet) [![codecov](https://codecov.io/gh/calestini/retrosheet/branch/master/graph/badge.svg)](https://codecov.io/gh/calestini/retrosheet) [![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Version: 0.1.0](https://img.shields.io/badge/version-0.1.0-green.svg)](https://img.shields.io/badge/version-0.1.0-green.svg)


A project to parse [retrosheet](https://www.retrosheet.org) baseball data in python. All data contained at Retrosheet site is copyright © 1996-2003 by Retrosheet. All Rights Reserved.

  _The information used here was obtained free of charge from and is copyrighted by Retrosheet.  Interested parties may contact Retrosheet at "www.retrosheet.org"_

## Motivation

The motivation behind this project is to enhance python-based baseball analytics, from data collection to advanced predictive modeling techniques.

---
## Before you start

If you are looking for a complete solution out of the box, check [Chadwick Bureau](http://chadwick-bureau.com/)
If you are looking for a quick way to check stats, see [Baseball-Reference](https://www.baseball-reference.com)
If you want a web-scrapping solution, check (pybaseball)[https://github.com/jldbc/pybaseball]

## Getting Started

### Downloading Package

Run the following code to create the folder structure
```bash
git clone https://github.com/calestini/retrosheet.git
```

### Downloading historical data to csv

**Note: This package is a work in progress, and the files are not yet fully parsed, and statistics not fully validated.**

The code below will save data from 1921 to 2017 in your machine. Be careful as it will take some time to download it all (10min with a decent machine and decent internet connection). Final datasets add up to ~ 3GB

```python
from retrosheet import Retrosheet
rs = Retrosheet()
rs.batch_parse(yearFrom=1921, yearTo=2017, batchsize=10) #10 files at a time
```
```bash
[========================================] 100.0% ... Completed 1921-1930
[========================================] 100.0% ... Completed 1931-1940
[========================================] 100.0% ... Completed 1941-1950
[========================================] 100.0% ... Completed 1951-1960
[========================================] 100.0% ... Completed 1961-1970
[========================================] 100.0% ... Completed 1971-1980
[========================================] 100.0% ... Completed 1981-1990
[========================================] 100.0% ... Completed 1991-2000
[========================================] 100.0% ... Completed 2001-2010
[========================================] 100.0% ... Completed 2011-2017
```

## Files it will download / create:

  - plays.csv
  - teams.csv
  - rosters.csv
  - lineup.csv
  - pitching.csv
  - fielding.csv
  - batting.csv
  - running.csv
  - info.csv

---
## Useful Links / References

  - Our own summary of Retrosheet terminology can be found [here](retrosheet/info.txt)
  - For the events file, the pitches field sometimes repeats over the following role, whenever there was a play (CS, SB, etc.). In these cases, the code needs to remove the duplication.
  - Main baseball statistics --> [here](https://en.wikipedia.org/wiki/Baseball_statistics)
  - Hit location diagram are [here](https://www.retrosheet.org/location.htm)
  - Link to downloads [here](https://www.retrosheet.org/game.htm)
  - [Glossary of Baseball](https://en.wikipedia.org/wiki/Glossary_of_baseball)
  - Information about the event files can be found [here](https://www.retrosheet.org/eventfile.htm)
  - Documentation on the datasets can be found [here](https://www.retrosheet.org/datause.txt)
  - Putouts and Assists [rules](https://baseballscoring.wordpress.com/site-index/putouts-and-assists/)


### Play Field in Event File:

  - What does 'BF' in '1/BF' stand for? bunt fly?
  - Why some specific codes for modifier are 2R / 2RF / 8RM / 8RS / 8RXD / L9Ls / RNT ?

## TODO

- [ ] Finish parsing pitches
- [ ] Clean-up code and logic
- [ ] Test primary stats with [game logs](https://www.retrosheet.org/gamelogs/)
- [X] Test innings ending in 3 outs
- [ ] Playoff files
- [ ] [Parks files](https://www.retrosheet.org/parkcode.txt)
- [ ] Player files
- [ ] Create sql export option
- [ ] Aggregate more advanced metrics
- [ ] Map out location
- [ ] Add additional data if possible
- [ ] Load [game-log data](https://www.retrosheet.org/gamelogs/)
- [ ] Load [player / manager/ umpire data](https://www.retrosheet.org/retroID.htm)

## Validating Stats - Spot Checks

  - Josh Donaldson (player_id = donaj001)

| Source | R | H | HR | SB |
|-|:-:|:-:|:-:|:-:|
| Official | 526 | 860 | 174 | 32 |
| ThisPackage | 521  | 853 | 173 | 32 |

  - Nelson Cruz (SEA Mariners)

| Source | R | H | HR | SB |
|-|:-:|:-:|:-:|:-:|
| Official | 768 | 1447 | 317 | 75 |
| ThisPackage | 761  | 1427 | 317 | 75 |
