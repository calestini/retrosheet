# retrosheet

[![Build Status](https://travis-ci.org/calestini/retrosheet.svg?branch=master)](https://travis-ci.org/calestini/retrosheet) [![codecov](https://codecov.io/gh/calestini/retrosheet/branch/master/graph/badge.svg)](https://codecov.io/gh/calestini/retrosheet) [![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Version: 0.1.0](https://img.shields.io/badge/version-0.1.0-green.svg)](https://img.shields.io/badge/version-0.1.0-green.svg)


A project to parse [retrosheet](https://www.retrosheet.org) baseball data in python. All data contained at Retrosheet site is copyright © 1996-2003 by Retrosheet. All Rights Reserved.

## Motivation

The motivation behind this project is to enhance python-based baseball analytics, from data collection to advanced predictive modeling techniques.

---
## Before you start

If you are looking for a complete solution out of the box, check [Chadwick Bureau](http://chadwick-bureau.com/)
If you are looking for a quick way to check stats, see [Baseball-Reference](https://www.baseball-reference.com)

## Getting Started

### Downloading Package

Run the following code to create the folder structure
```bash
git clone https://github.com/calestini/retrosheet.git
```

### Downloading historical data to csv

**Note: This package is a work in progress, and the files are not yet fully parsed, and statistics not fully validated.**

The code below will save data from 1921 to 2017 in your machine. Be careful as it will take some time to download it all (~10 min if the datasets for each year are locally stored).

```python
from retrosheet import Retrosheet
rs = Retrosheet()
rs.get_data(yearFrom=1921, yearTo=2017)
rs.save_csv()
```
```bash
>>> [========------------------] 33.5% ... 1959
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
- [ ] Test primary stats
- [X] Test innings ending in 3 outs
- [ ] Playoff files
- [ ] [Parks files](https://www.retrosheet.org/parkcode.txt)
- [ ] Player files
- [ ] Create sql export option
- [ ] Aggregate more advanced metrics
- [ ] Map out location
- [ ] Add additional data if possible
