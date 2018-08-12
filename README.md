# retrosheet

A project to parse [retrosheet](https://www.retrosheet.org) baseball data in python

 - Documentation on the play datasets can be found [here](https://www.retrosheet.org/datause.txt)

 - Link to downloads [here](https://www.retrosheet.org/game.htm)

Collaborators:
  - [Cathy](https://github.com/cathyhax)
  - [Lucas](https://github.com/calestini)

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

```bash
python main.py

>>> [========------------------] 33.5% ... 1959
```

## Missing Parsing

  - Plays
  - Info variable names
  - Pich counts
  - Datetime for each game
