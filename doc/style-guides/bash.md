## POSIX versus Bash

There is a lot of debate out there about using POSIX-compliant versus Bash-specific syntax (eg. `[` versus `[[`, respectively). Using POSIX-compliant syntax is more portable across different shells, but using Bash-specific syntax can be cleaner and conducive to fewer bugs.

Here we do not write system-level code; we write user-level code. We do not need portabaly outside of Bash because any self-respecting user-oriented Unix-like system has a Bash interpreter. We prefer cleaner, less error-prone code. We therefore do not restrain ourselves from using Bash-specific syntax.

## Variable names

Use lower case names for variables, and use underscores as needed to improve readabilty.

Rationale:

- save our pinkie fingers some needless strain.
- use the same convention we use for Python code.

## Single versus double brackets

We use double brackets. Everywhere. For example:

```sh
# Not ok
if [ $myvar = 42 ]; then
    echo "this is the answer"
fi

# Ok
if [[ $myvar = 42 ]]; then
    echo "this is the answer"
fi
```

Rationale: the double brackets syntax is a Bash-specific feature that is more powerful than the POSIX-compliant single bracket. Double brackets are also safer to use when variables are undefined. In the example above, if `$myvar` is undefined, the single bracket syntax will result in a syntax-like error while the double bracket syntax will work as expected.

# Double parentheses versus double brackets

# -eq, ==, =

# Function docstrings

# Use of curly braces around variable names
