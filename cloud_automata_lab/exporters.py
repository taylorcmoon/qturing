"""exporters.py — multi-language code generation for Turing machines.

``export(machine, language)`` renders a ``TuringMachineSpec`` as a
self-contained, runnable program in the target language.

Supported targets: ``wolfram``, ``python``, ``javascript``, ``go``, ``c``.

Author:  Taylor Moon <taylorcmoon>
License: MIT
"""
from __future__ import annotations

import json
import re
from typing import Literal

from .types import TuringMachineSpec
from .wolfram import to_wolfram

ExportLanguage = Literal["wolfram", "python", "javascript", "go", "c"]
EXPORT_LANGUAGES: list[tuple[ExportLanguage, str]] = [
    ("wolfram", "Wolfram"),
    ("python", "Python"),
    ("javascript", "JavaScript"),
    ("go", "Go"),
    ("c", "C"),
]


def export(machine: TuringMachineSpec, language: ExportLanguage) -> str:
    if language == "wolfram":
        return to_wolfram(machine)
    if language == "python":
        return _to_python(machine)
    if language == "javascript":
        return _to_javascript(machine)
    if language == "go":
        return _to_go(machine)
    if language == "c":
        return _to_c(machine)
    raise ValueError(f"Unknown export language: {language}")


def _to_python(m: TuringMachineSpec) -> str:
    rows = "\n".join(
        f"    ({json.dumps(t.state)}, {json.dumps(t.read)}): "
        f"({json.dumps(t.next_state)}, {json.dumps(t.write)}, {json.dumps(t.move)}),"
        for t in m.transitions
    )
    return f"""# {m.name}

BLANK  = {json.dumps(m.blank_symbol)}
START  = {json.dumps(m.start_state)}
ACCEPT = {json.dumps(m.accept_state)}
REJECT = {json.dumps(m.reject_state)}

TRANSITIONS = {{
{rows}
}}

def run(tape_str, max_steps=10_000):
    tape  = list(tape_str or BLANK)
    head  = 0
    state = START
    steps = 0

    while steps < max_steps:
        if state == ACCEPT:
            return "ACCEPT", "".join(tape).strip(BLANK), steps
        if state == REJECT:
            return "REJECT", "".join(tape).strip(BLANK), steps

        while head < 0:
            tape.insert(0, BLANK)
            head = 0
        while head >= len(tape):
            tape.append(BLANK)

        key = (state, tape[head])
        if key not in TRANSITIONS:
            return "REJECT", "".join(tape).strip(BLANK), steps

        state, tape[head], move = TRANSITIONS[key]
        if move == "R":
            head += 1
        elif move == "L":
            head -= 1
        steps += 1

    return "TIMEOUT", "".join(tape).strip(BLANK), steps


result, final_tape, steps = run({json.dumps(m.input_tape)})
print(f"Result:     {{result}}")
print(f"Final tape: {{final_tape}}")
print(f"Steps:      {{steps}}")
"""


def _to_javascript(m: TuringMachineSpec) -> str:
    rows = "\n".join(
        f"  '{json.dumps([t.state, t.read])}': "
        f"[{json.dumps(t.next_state)}, {json.dumps(t.write)}, {json.dumps(t.move)}],"
        for t in m.transitions
    )
    return f"""// {m.name}

const BLANK  = {json.dumps(m.blank_symbol)};
const START  = {json.dumps(m.start_state)};
const ACCEPT = {json.dumps(m.accept_state)};
const REJECT = {json.dumps(m.reject_state)};

const TRANSITIONS = {{
{rows}
}};

function run(tapeStr, maxSteps = 10_000) {{
  const tape = [...(tapeStr || BLANK)];
  let head = 0, state = START;

  for (let steps = 0; steps < maxSteps; steps++) {{
    if (state === ACCEPT) return {{ result: "ACCEPT", tape: tape.join(""), steps }};
    if (state === REJECT) return {{ result: "REJECT", tape: tape.join(""), steps }};

    while (head < 0) {{ tape.unshift(BLANK); head = 0; }}
    while (head >= tape.length) tape.push(BLANK);

    const entry = TRANSITIONS[JSON.stringify([state, tape[head]])];
    if (!entry) return {{ result: "REJECT", tape: tape.join(""), steps }};

    const [nextState, write, move] = entry;
    tape[head] = write;
    state = nextState;
    if (move === "R") head++;
    else if (move === "L") head--;
  }}

  return {{ result: "TIMEOUT", tape: tape.join(""), steps: maxSteps }};
}}

const {{ result, tape, steps }} = run({json.dumps(m.input_tape)});
console.log(`Result:     ${{result}}`);
console.log(`Final tape: ${{tape}}`);
console.log(`Steps:      ${{steps}}`);
"""


def _to_go(m: TuringMachineSpec) -> str:
    rows = "\n".join(
        f'\t{{"{t.state}", "{t.read}"}}: {{"{t.next_state}", "{t.write}", "{t.move}"}},'
        for t in m.transitions
    )
    return f"""// {m.name}
package main

import (
\t"fmt"
\t"strings"
)

type step struct{{ nextState, write, move string }}

var transitions = map[[2]string]step{{
{rows}
}}

func run(tapeStr string, maxSteps int) (string, string, int) {{
\ttape := strings.Split(tapeStr, "")
\tif tapeStr == "" {{
\t\ttape = []string{{"{m.blank_symbol}"}}
\t}}
\thead, state := 0, "{m.start_state}"

\tfor s := 0; s < maxSteps; s++ {{
\t\tswitch state {{
\t\tcase "{m.accept_state}":
\t\t\treturn "ACCEPT", strings.Join(tape, ""), s
\t\tcase "{m.reject_state}":
\t\t\treturn "REJECT", strings.Join(tape, ""), s
\t\t}}

\t\tfor head < 0 {{
\t\t\ttape = append([]string{{"{m.blank_symbol}"}}, tape...)
\t\t\thead = 0
\t\t}}
\t\tfor head >= len(tape) {{
\t\t\ttape = append(tape, "{m.blank_symbol}")
\t\t}}

\t\tt, ok := transitions[[2]string{{state, tape[head]}}]
\t\tif !ok {{
\t\t\treturn "REJECT", strings.Join(tape, ""), s
\t\t}}

\t\ttape[head] = t.write
\t\tstate = t.nextState
\t\tswitch t.move {{
\t\tcase "R":
\t\t\thead++
\t\tcase "L":
\t\t\thead--
\t\t}}
\t}}
\treturn "TIMEOUT", strings.Join(tape, ""), maxSteps
}}

func main() {{
\tresult, finalTape, steps := run("{m.input_tape}", 10_000)
\tfmt.Printf("Result:     %s\\n", result)
\tfmt.Printf("Final tape: %s\\n", finalTape)
\tfmt.Printf("Steps:      %d\\n", steps)
}}
"""


def _c_char(ch: str) -> str:
    """Return a C char literal for a single character."""
    escaped = {"'": "\\'", "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t"}
    return f"'{escaped.get(ch, ch)}'"


def _to_c(m: TuringMachineSpec) -> str:
    def state_id(s: str) -> str:
        return "S_" + re.sub(r"[^A-Za-z0-9]", "_", s).upper()

    # Preserve declaration order: start, accept, reject first, then any extras
    seen: dict[str, None] = {}
    for s in [m.start_state, m.accept_state, m.reject_state]:
        seen[s] = None
    for t in m.transitions:
        seen[t.state] = None
        seen[t.next_state] = None
    states = list(seen)

    enum_vals = "\n    ".join(f"{state_id(s)} = {i}," for i, s in enumerate(states))

    move_int = {"L": -1, "S": 0, "R": 1}
    rows = "\n".join(
        f"    {{ {state_id(t.state)}, {_c_char(t.read[0])}, {_c_char(t.write[0])}, "
        f"{move_int[t.move]:+d}, {state_id(t.next_state)} }},"
        for t in m.transitions
    )

    blank = m.blank_symbol[0] if m.blank_symbol else "_"

    return f"""\
/* {m.name}
 * Compile: cc -O2 -o tm tm.c
 * Run:     ./tm
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLANK     {_c_char(blank)}
#define MAX_STEPS 10000
#define TAPE_INIT 256

typedef enum {{
    {enum_vals}
    S_COUNT
}} State;

typedef struct {{
    State state;
    char  read;
    char  write;
    int   move;   /* -1=L  0=S  +1=R */
    State next;
}} Rule;

static const Rule TRANSITIONS[] = {{
{rows}
}};
#define N_RULES (int)(sizeof(TRANSITIONS) / sizeof(TRANSITIONS[0]))

typedef struct {{ char *buf; int cap; int origin; }} Tape;

static void tape_init(Tape *t, const char *input) {{
    t->cap    = TAPE_INIT;
    t->buf    = (char *)malloc(t->cap);
    t->origin = t->cap / 2;
    memset(t->buf, BLANK, t->cap);
    int n = (int)strlen(input);
    for (int i = 0; i < n; i++)
        t->buf[t->origin + i] = input[i];
}}

static char tape_get(Tape *t, int pos) {{
    int idx = t->origin + pos;
    if (idx < 0 || idx >= t->cap) return BLANK;
    return t->buf[idx];
}}

static void tape_set(Tape *t, int pos, char ch) {{
    while (t->origin + pos < 0) {{
        char *nb = (char *)malloc(t->cap * 2);
        memset(nb, BLANK, t->cap * 2);
        memcpy(nb + t->cap, t->buf, t->cap);
        free(t->buf);
        t->buf = nb; t->origin += t->cap; t->cap *= 2;
    }}
    while (t->origin + pos >= t->cap) {{
        t->buf = (char *)realloc(t->buf, t->cap * 2);
        memset(t->buf + t->cap, BLANK, t->cap);
        t->cap *= 2;
    }}
    t->buf[t->origin + pos] = ch;
}}

static void tape_print(Tape *t) {{
    int lo = 0, hi = 0;
    for (int i = -t->origin; i < t->cap - t->origin; i++) {{
        char c = tape_get(t, i);
        if (c != BLANK) {{ if (i < lo) lo = i; if (i > hi) hi = i; }}
    }}
    for (int i = lo; i <= hi; i++) putchar(tape_get(t, i));
}}

int main(void) {{
    Tape  tape;
    tape_init(&tape, {json.dumps(m.input_tape)});
    State state  = {state_id(m.start_state)};
    int   head   = 0;
    const char *result = "TIMEOUT";

    for (int step = 0; step < MAX_STEPS; step++) {{
        if (state == {state_id(m.accept_state)}) {{ result = "ACCEPT"; break; }}
        if (state == {state_id(m.reject_state)}) {{ result = "REJECT"; break; }}

        char sym   = tape_get(&tape, head);
        int  found = 0;
        for (int i = 0; i < N_RULES; i++) {{
            if (TRANSITIONS[i].state == state && TRANSITIONS[i].read == sym) {{
                tape_set(&tape, head, TRANSITIONS[i].write);
                state  = TRANSITIONS[i].next;
                head  += TRANSITIONS[i].move;
                found  = 1;
                break;
            }}
        }}
        if (!found) {{ result = "REJECT"; break; }}
    }}

    printf("Result:     %s\\n", result);
    printf("Final tape: "); tape_print(&tape); printf("\\n");
    free(tape.buf);
    return 0;
}}
"""
