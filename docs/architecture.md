# Architecture

How the Python code is built: packages, modules, the main classes and who calls whom. What the game is lives in [`design/`](../design/), in domain terms; this page is about the code that implements it.

It describes only what exists. Each session updates it at wrap-up when the code structure changes ([Working with Claude](../WorkingWithClaude.md#how-a-session-works)). Diagrams show the classes and how they connect; their fields and methods are read in the code, so the diagrams do not drift from it.

## Packages

```
src/alone_against_fear/
  __main__.py       python -m alone_against_fear: the terminal
  dice.py           dice codes, chances, dice sources (shared by content and engine)
  engine/           the game: state and the engine API
    state.py        Campaign, Character, Mission, History, TownMap, Box (plain data)
    town.py         sheets, neighbours, distance (pure geometry)
    game.py         Game: the only way the state changes
    protocol.py     requests, events, Interface: how the engine talks to an interface
    loop.py         play(): the game loop
  interface/        what answers the engine: reads input, shows the game
    scripted.py     ScriptedInterface: prepared answers, for tests
    terminal.py     TerminalInterface and main(): play in the terminal
  content/          the rules text: YAML files, their loader and model
    loader.py       YAML files → Content
    model.py        Content, Table, Entry, Roll, CatalogueTable, the checks
    catalogue.yaml  tables known but not copied yet
    tables/         one YAML file per copied table
```

Rules that hold for every package ([`CLAUDE.md`](../CLAUDE.md)): the engine never reads input or prints, and the game state refers to content by ID only and never holds code.

**Logging.** Every module logs to a child of the `alone_against_fear` logger (standard `logging`): rolls at DEBUG, state changes at INFO. Every answer to a request is logged at INFO (`answer move: (2, 3)`). The engine only emits; the interface decides where the log goes: the terminal writes it to `logs/<date-time>.log` (git-ignored) at DEBUG. Tests read it with `caplog`.

## `dice`: dice codes and dice sources

```mermaid
classDiagram
    direction LR
    DiceCode ..> Dice : roll(dice)
    Chance ..> Dice : roll(dice)
    DiceCode --> DiceRoll : gives
    Chance --> ChanceRoll : gives
    Dice <|.. RandomDice
    Dice <|.. ScriptedDice
    class Dice {
        <<protocol>>
    }
```

- **Dice codes are parsed from the book's notation** (`"2d6+1"`, `"d6 x d6"`, `"12+d6"`, `"d66"`) and shown back in a standard form (`str(code)`). `Combine` says how the dice make the total: sum, product (`d6xd6`) or digits (`d66`). A d3 is a d6 halved. `"x in 6"` is a `Chance`, true on a die showing x or less.
- **Every roll goes through a `Dice` source** that only rolls d6: `RandomDice(seed)` for play and reproducible tests (with no seed it picks one and logs it, so a game's dice can be rolled again), `ScriptedDice([...])` for rule tests that state the faces shown. A result keeps every face, so rules can read the natural die.
- **Plain data.** Codes and results are frozen dataclasses; the content loader stores a table's dice in standard form and its coverage check asks `DiceCode.results()`.

## `engine`: the game state and the engine API

```mermaid
classDiagram
    direction LR
    Game --> "1" Campaign : campaign
    Game ..> Dice : dice
    Game ..> Content : content
    Campaign --> "1" TownMap : map
    Campaign --> "1" History : history
    Campaign --> "0..1" Character : character
    Character --> "1" History : history
    Character --> "0..1" Mission : mission
    Mission --> "1" History : history
    TownMap --> "*" Box : boxes by Position
```

- **The state is mutable plain data**: dataclasses of numbers, strings, enums, lists, dicts and counters, content referred to by ID. A test walks the whole campaign to check it holds no code, so saving it later is turning it into a dict.
- **Levels nest as in the design**: the campaign never forgets, a new character replaces the last one (and its history), a new mission replaces the last one. `Level` names them; `Game.history(level)` finds the right one.
- **The history counts, it does not log**: `Happened.PLAYED`, `FOUND`, `KILLED` per ID, plus keywords. The rules only ask "has it happened?" and "how many times?". The story of the game goes to the log file instead.
- **`Game` is the only writer.** It checks only what the state cannot hold (no character, unknown mission, negative amount, missing item) and raises `GameError`; the rules about limits come with their tasks. 
- **The town is one grid** (`town.py`). `Position` is a `(column, row)` named tuple, for a box in the town and for a sheet in the grid of sheets. A sheet is a 5×6 block (`sheet_of`); `neighbours(position, sheets)` are the 8 boxes around that lie on an attached sheet (open edges are walls), `distance` is the larger of the column and row gaps. Nothing geometric is stored.
- **Moves.** The engine offers `targets(kind)` and the interface picks; `move(to, kind)` refuses anything else, numbers the box, runs the Food upkeep (every 5th box number on the campaign clock: 1 Food, else 1 Life) and returns an `Arrival`. `MoveKind` has `NORMAL` and `ESCAPE` for now. `choose_home` is box 1 (first sheet, once); `add_sheet` attaches a sheet against a full one.
- **A box remembers** its places (IDs), `searched` and `marks`.
- **The dice are not part of the state**: play is random, so a resumed campaign rolls fresh dice.

## `engine.protocol` and `engine.loop`: the engine asks, the interface answers

```mermaid
sequenceDiagram
    participant UI as Interface (terminal, scripted)
    participant P as play()
    participant Game
    P->>Game: create_character (placeholder), if none
    P->>UI: ask(Choose HOME, 30 boxes), if no Home yet
    UI-->>P: a box
    P->>Game: choose_home
    P->>UI: tell(Arrival)
    loop each turn, until dead, insane or quit
        P->>UI: ask(Choose ACTION, move / quit)
        UI-->>P: move
        P->>Game: targets()
        P->>UI: ask(Choose MOVE, targets)
        UI-->>P: a box
        P->>Game: move(box)
        P->>UI: tell(Arrival)
    end
    P->>UI: tell(Ended)
```

```mermaid
classDiagram
    direction LR
    Interface <|.. ScriptedInterface
    Interface <|.. TerminalInterface
    Interface ..> Choose : ask
    Interface ..> Arrival : tell
    Interface ..> Ended : tell
    TerminalInterface ..> Game : reads
    class Interface {
        <<protocol>>
    }
```

- **Callback protocol.** The engine holds the interface and calls it while the rules run: `ask(request)` returns the player's answer at once, `tell(event)` reports what happened, in order. A rule deep inside another (a fight inside an event inside an arrival) asks the same way. Chosen over generators (every function on the path would need `yield from`) and a state machine (every multi-step rule cut into states). The price: the game can only be saved between turns, which fits "saving = saving the campaign"; a GUI would run the engine in a thread.
- **Requests and events are plain data.** `Choose(topic, options)` is the only request so far; the topic tells the interface how to show it (a map for `HOME` and `MOVE`). Other shapes (a number, an order) come with the tasks that need them. Events are `Arrival` (from `Game.move`, and for Home) and `Ended`.
- **The answer must be one of the options.** `loop.ask` refuses anything else with `GameError`, logs the answer and returns the option itself. A scripted answer that is not an option fails the test; the terminal checks the input before answering.
- **`Quit`** may be raised by an interface at any request: the game ends with `End.QUIT` (the terminal raises it on Ctrl-D or Ctrl-C).
- **The loop** (`play(game, interface) -> End`): creates the placeholder character if there is none (Life 8, Sanity 8, Food d6, until E6), asks for Home if it is not chosen, then turns: an action (`MOVE` or `QUIT`), then a box among `Game.targets()`, listed in reading order. It ends at 0 Life (dead, checked first, [ruling](../design/rulings.md#character)), 0 Sanity (insane) or quit. Arriving, Search and free actions are hook points for book mode (E5a, E5b) and later.
- **Interfaces read the game, never change it**: the terminal reads `Game` to draw the status line and the map; only its answers move the game on.

## `interface`: scripted and terminal

- **`ScriptedInterface(answers)`** gives the answers in order, remembers what was `asked` and `told`, and raises `ScriptError` when it runs out. Used by the scenario tests.
- **`TerminalInterface(game, input_fn, output_fn)`**: a status line before each action, a map of the attached sheets with numbered options (`[1]`), `@` where the character stands, `H` for Home and the last number of visited boxes; a wrong choice is asked again. Input and output are passed in so tests type lines.
- **`main(argv)`** (console script `alone-against-fear`, or `python -m alone_against_fear`): `--seed`, `--log-dir` (default `logs`); sets up the log file, loads the content, plays.

## `content`: the rules text

The book's text, copied into YAML, loaded once and read by ID. The format (files, IDs, fields) and the reasons behind it are in [rules text in YAML](content.md).

```mermaid
flowchart LR
    yaml[(YAML files<br/>catalogue.yaml, tables/)] --> load["load_content()"]
    load --> content[Content]
    content --> checks["coverage_problems()<br/>reference_problems()<br/>note_problems()"]
    content --> lookup["content.table(id)<br/>content.entry(id)<br/>table.entry_for(result)"]
    checks --> tests[tests]
    lookup --> tests
```

```mermaid
classDiagram
    direction LR
    Content --> "*" Table : tables
    Content --> "*" CatalogueTable : catalogue
    Content --> "*" Entry : entries, every one by ID
    Table --> "1..*" Entry : entries
    Entry --> "1" Roll : roll
    Entry --> "0..1" Table : nested table
```

- **Read-only.** Every class is a frozen dataclass: content never changes once loaded. The game state will hold IDs pointing into it, never copies.
- **`Content` indexes every entry by ID**, nested and named ones included, so `content.entry("mission.bring_home_the_bacon")` and `content.entry("table.random_encounter.3.3-5")` both work. `id in content` is true for a table, an entry or a catalogued table: that is what references are checked against.
- **A nested table has the ID of the entry that holds it** (`table.random_encounter.3`), and its entries' notes point to the top table's `notes`.
- **Two kinds of error.** The loader raises `ContentError` when a file is malformed: unknown key, bad roll, unknown dice, an ID defined twice. The checks return lists of problems (gaps and overlaps in the dice, references or notes pointing to nothing), so a test can show every problem at once.
- **A table's `dice`** is any dice code, kept in standard form; the coverage check asks `DiceCode` for its results.
- **`KINDS`** lists the first segments an ID may have (`table`, `mission`); a YAML batch adds the kinds it needs.

Used by: the tests, and `Game.start_mission`, which checks mission IDs. Book mode (E5a) will be the first real engine user.

## Tests

| File | What it covers |
| --- | --- |
| `tests/test_content.py` | the real content: the checks over every table, then what each table says, written from the book |
| `tests/test_content_validation.py` | each check on a small made-up content, so a check that never fires cannot pass unnoticed |
| `tests/test_dice.py` | every dice code of the Dice Codes section, chances, seeded and scripted dice |
| `tests/test_game_state.py` | the game state through `Game`: levels, character, missions, boxes, history, plain data, logging |
| `tests/test_town_map.py` | sheets, neighbours, distance, moves, numbering, Food upkeep, new sheets |
| `tests/test_game_loop.py` | scenarios through a scripted interface: walking 10 boxes, what the engine asks, answers refused and logged, how a game ends |
| `tests/test_terminal.py` | the terminal played with typed lines: walking 10 boxes, the map, wrong choices, end of input, the log file |
| `tests/test_smoke.py` | the package imports |
