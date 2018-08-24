# retrosheet

[![Build Status](https://travis-ci.org/calestini/retrosheet.svg?branch=master)](https://travis-ci.org/calestini/retrosheet) [![codecov](https://codecov.io/gh/calestini/retrosheet/branch/master/graph/badge.svg)](https://codecov.io/gh/calestini/retrosheet) [![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A project to parse [retrosheet](https://www.retrosheet.org) baseball data in python. All data contained at Retrosheet site is copyright © 1996-2003 by Retrosheet. All Rights Reserved.

## Motivation

The motivation behind this project is to enhance python-based baseball analytics from data collection to advanced predictive modeling techniques.

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

**Note: This package is a work in progress, and the files are not yet fully parsed.**

The code below will load data from 1921 to 2017. Be careful as it will take some time to download it all (~10 min).

```python
from retrosheet import Retrosheet
rs = Retrosheet()
rs.get_data(yearFrom=1921, yearTo=2017)
rs.save_csv()
```
```bash
>>> [========------------------] 33.5% ... 1959
```

### Parsing plays

We can also visually check all plays for a sequence (without statistics for now). The code below looks for all plays in an inning, printing the diamond for each play/event. The diamond separates H and B location to make it easier to see how many runs happened in the sequence.


```python
from retrosheet import Event

event_sequence = [
'S9','S7.1-2','34/SH.2-3;1-2','S9.3-H;2-3',
'W.1-2''S8.3-H;2-H;1X3(8254)','4']

  play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0}
  event = Event() #start event with no play

  print ('Beginning of the play:\n')
  for string in event_sequence:
      event.str = string
      event.decipher()
      event._print_diamond()
```
```bash
Play: S9
|---------[ 0 ]-----------|
|-------------------------|
|----[ 0 ]------[ 1 ]-----|
|-------------------------|
|------[ 0 ]--[ 0 ]-------|
|-------------------------|
Runs: 0	Outs: 0

(...)

Play: 4
|---------[ 0 ]-----------|
|-------------------------|
|----[ 0 ]------[ 1 ]-----|
|-------------------------|
|------[ 3 ]--[ 0 ]-------|
|-------------------------|
Runs: 3	Outs: 3

```

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

## Notation Questions

  - Interesting event play sequence: *'S9.3-H(TUR);2-H(TUR);1-3;BX2(93)'*. It is a single, but the baserunner tries to go for 2B and is out.

### Play Field in Event File:

  - What does 'BF' in '1/BF' stand for? bunt fly?
  - Why some specific codes for modifier are 2R / 2RF / 8RM / 8RS / 8RXD / L9Ls / RNT ?

## TODO

  - Plays:
    - Test primary stats
    - Test innings ending in 3-out
  - Parse other files
    - Playoff files
    - Additional files
    - Player / [Parks files](https://www.retrosheet.org/parkcode.txt)
