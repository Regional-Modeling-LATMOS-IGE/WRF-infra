## POSIX versus Bash

There is a lot of debate out there about using POSIX-compliant versus Bash-specific syntax (eg. `[` versus `[[`, respectively). Using POSIX-compliant syntax is more portable across different shells, but using Bash-specific syntax can be cleaner and conducive to fewer bugs.

Here we do not write system-level code; we write user-level code. We do not need portabaly outside of Bash because any self-respecting user-oriented Unix-like system has a Bash interpreter. We prefer cleaner, less error-prone code. We therefore do not restrain ourselves from using Bash-specific syntax.

## Indentation

Use 4 spaces (no tabs) for each level of indentation.

Rationale: isn't that a universally accepted convention?

## Variable names

Use lower case names for variables, and use underscores as needed to improve readabilty.

Rationale:

- save our pinkie fingers some needless strain.
- use the same convention we use for Python code.

## Quotes

Do not use unnecessary quotes:


```sh
# Not OK
my_variable="/home/myself"

# OK
my_variable=/home/myself
```

Rationale: this is simpler and more readable.

Where quotes are needed, use double-quotes by default, and single quotes where needed, for example:

```sh
# OK
echo 'I want to show you what the dollar sign looks like: $'
```

## Single versus double brackets

We use double brackets. Everywhere. For example:

```sh
# Not OK
if [ $myvar -eq 42 ]; then
    echo "this is the answer"
fi

# OK
if [[ $myvar -eq 42 ]]; then
    echo "this is the answer"
fi
```

Rationale: the double brackets syntax is a Bash-specific feature that is more powerful than the POSIX-compliant single bracket. Double brackets are also safer to use when variables are undefined. In the example above, if `$myvar` is undefined, the single bracket syntax will result in a syntax-like error while the double bracket syntax will work as expected.

# Double square brackets versus double parentheses

Use double square brackets everywhere you can. Use double parentheses when you actually need arithmetics.

```sh
# OK
if [[ $my_var -eq 0 ]]; then
    echo "my_var is zero"
fi

# Not OK
if (( my_var == 0 )); then
    echo "my_var is zero"
fi
```

Rationale: with this choice, the syntax is generally more consistent throughout scripts. We rarely need to perform many arithemetic operations in a Bash script. If you do, you should probably use Python instead.

# Comparison operators (-eq, -ne, =, ==, !=, etc)

The following operators are used to compare numbers inside double square braquets `[[ ... ]]`: `-eq`, `-ne`, `-lt`, `-le`, `-gt`, `-ge`.

The following operators are used to compare strings inside double square braquets `[[ ... ]]`: `==`, `!=`. The operator `=` can also be used for equality testing in this context, but we prefer to use `==` instead. Rationale:
 - It is more intuitive, because most other languages use `==` for equality testing, while `=` is generally used for assignment.
 - `==` is more flexible than `=`: the former can be used for pattern matching.

# Function docstrings

# Use of curly braces around variable names
