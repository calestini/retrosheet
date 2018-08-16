# retrosheet

[![Build Status](https://travis-ci.org/calestini/retrosheet.svg?branch=master)](https://travis-ci.org/calestini/retrosheet) [![codecov](https://codecov.io/gh/calestini/retrosheet/branch/master/graph/badge.svg)](https://codecov.io/gh/calestini/retrosheet) [![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A project to parse [retrosheet](https://www.retrosheet.org) baseball data in python. All data contained at Retrosheet site is copyright © 1996-2003 by Retrosheet. All Rights Reserved.

 - Documentation on the datasets can be found [here](https://www.retrosheet.org/datause.txt)

 - Information about the event files can be found [here](https://www.retrosheet.org/eventfile.htm)

 - Hit location diagram are [here](https://www.retrosheet.org/location.htm)

 - Link to downloads [here](https://www.retrosheet.org/game.htm)

Collaborators:
  - [Cathy](https://github.com/cathyhax)
  - [Lucas](https://github.com/calestini)

Other resources:
  - [Glossary of Baseball](https://en.wikipedia.org/wiki/Glossary_of_baseball)

---

## Getting Started

### Downloading Package

Run the following code to create the folder structure
```bash
git clone https://github.com/calestini/retrosheet.git
```

### Downloading historical data to csv

**Note: This package is a work in progress, and the files are not yet fully parsed.**

The code below will load data from 1921 to 2017. Be careful as it will take some time to download it all.

```python
from retrosheet import Parser
parser = Parser()
info, starting, plays, er, subs, comments, rosters, teams = parser.parse_years(yearFrom=1921, yearTo=2017, save_to_csv=True)
```
```bash
>>> [========------------------] 33.5% ... 1959
```

### Parsing plays

We can also visually check all plays for a sequence (without statistics for now). The code below looks for all plays in an inning, priting the diamond after each play. The diamond separates H and B location for us to visualize how many runs
happened in the sequence.


```python
from retrosheet import Event

event_sequence = [
'S9','S7.1-2','34/SH.2-3;1-2','S9.3-H;2-3',
'W.1-2''S8.3-H;2-H;1X3(8254)','4']

  play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0}
  event = Event('NP', play) #start event with no play

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

Play: S7.1-2
|---------[ 1 ]-----------|
|-------------------------|
|----[ 0 ]------[ 1 ]-----|
|-------------------------|
|------[ 0 ]--[ 0 ]-------|
|-------------------------|
Runs: 0	Outs: 0

Play: 34/SH.2-3;1-2
|---------[ 1 ]-----------|
|-------------------------|
|----[ 1 ]------[ 0 ]-----|
|-------------------------|
|------[ 0 ]--[ 0 ]-------|
|-------------------------|
Runs: 0	Outs: 1

Play: S9.3-H;2-3
|---------[ 0 ]-----------|
|-------------------------|
|----[ 1 ]------[ 1 ]-----|
|-------------------------|
|------[ 1 ]--[ 0 ]-------|
|-------------------------|
Runs: 1	Outs: 1

Play: W.1-2S8.3-H;2-H;1X3(8254)
|---------[ 0 ]-----------|
|-------------------------|
|----[ 0 ]------[ 1 ]-----|
|-------------------------|
|------[ 3 ]--[ 0 ]-------|
|-------------------------|
Runs: 3	Outs: 2

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
## Useful Notes

  - Our own summary of Retrosheet terminology can be found [here](retrosheet/info.txt)
  - For the events file, the pitches field sometimes repeats over the following role, whenever there was a play (CS, SB, etc.). In these cases, the code needs to remove the duplication.

## Notation questions
  - Interesting event play sequence: *'S9.3-H(TUR);2-H(TUR);1-3;BX2(93)'*. It is a single, but the baserunner tries to go for second and is out.

### Play Field in Event File:
  - What does 'BF' in '1/BF' stand for? bunt fly?
  - Why some specific codes for modifier are 2R / 2RF / 8RM / 8RS / 8RXD / L9Ls / RNT ?

## Missing Parsing

  - Plays [======**50%**-----]:
    - Missing trajectory, errors, RBIs and player-related to each event.
    - Need to test if all innings end in 3 out. Ran some spot checks and it seems to work.
  - Pich counts [======**70%**-----]
    - Need to spot check and compare to official statistics
  - Other files
    - Playoff files
    - Additional files
