import enum
import logging
import re
import typing
from collections import deque

logger = logging.getLogger("tokamak")


@enum.unique
class ParamToken(enum.Enum):
    """
    Parameters in a path are inside curly braces and may
    include a colon and a regex.

    This enum represents the _only_ characters our parser will look for to extract
    the elements of the Dynamic node.
    """

    LEFT_BRACE = "{"
    COLON = ":"
    RIGHT_BRACE = "}"
    STAR = "*"  # MATCH ALL pattern


class DynamicParseNode:
    MATCH_UP_TO_SLASH = "[^/]+"
    VALID_NAME_REGEX = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)")
    __slots__ = ["raw", "name", "regex", "_pattern"]

    def __init__(self, raw: str, name: str, regex: typing.Optional[str] = None):
        if any(
            (
                len(raw) == 0,
                len(name) == 0,
                not isinstance(raw, str),
                not isinstance(name, str),
            )
        ):
            raise ValueError("Must pass non-empty strings for `raw` and `name`")
        self.raw = raw
        self.name = name
        if regex == ParamToken.STAR.value or regex is None:
            self.regex: str = self.MATCH_UP_TO_SLASH
        else:
            self.regex = regex
        self._pattern: typing.Optional[re.Pattern] = None

        match = self.VALID_NAME_REGEX.match(self.name)
        if not self.name or not match:
            raise ValueError("Invalid parameter name")
        if not match.end() == len(self.name):
            raise ValueError("Invalid parameter name")

    def __eq__(self, other) -> bool:  # type: ignore
        return (
            self.raw == other.raw
            and self.name == other.name
            and self.regex == other.regex
        )

    @property
    def pattern(self) -> re.Pattern:
        if self._pattern is not None:
            return self._pattern

        pat: str = "(?P<{name}>{regex})".format(name=self.name, regex=self.regex)
        self._pattern = re.compile(pat)
        return self._pattern

    def match(
        self, query: str
    ) -> typing.Tuple[int, typing.Optional[typing.Dict[str, str]]]:
        match = self.pattern.match(query)
        if match:
            return match.end(), match.groupdict()
        return -1, None


def first_nonequal_idx(left: str, right: str) -> int:
    """
    Find first string index where left and right strings do not match

        In [1]: first_nonequal_idx("", "californian")
        Out[1]: 0

        In [2]: first_nonequal_idx("aba", "abc")
        Out[2]: 2

    Note, if the strings match, the first-non-equal index will be equal to the length of the string:

        In [3]: first_nonequal_idx("aba", "aba")
        Out[3]: 3
    """
    idx = 0
    max_search_len = min(len(left), len(right))
    while idx < max_search_len and left[idx] == right[idx]:
        idx += 1
    return idx


def parse_dynamic(path: str) -> typing.Iterator[typing.Union[str, "DynamicParseNode"]]:
    """
    This method discerns the dynamic elements in a string.

    There are some assumptions involved:

      - This will be used in URI paths, so regexes will be for typically allowed URI characters
      - A dynamic element _always_ begins with the char `{` and ends with the char `}`
      - A colon separates a parameter name from a regex, which are optional.
      - It is possible to include nested braces as part of a regex, but they must be matched:
        - This is fine: `{name:[a-zA-Z]{10}}`
        - This (a valid regex) will raise an exception: `{code:[}{}]}`
      - We may later construct a named pattern out of this,
        so any parenthesis in the pattern will likely break.

    Returns a generator that yields in turn, static strings and DynamicParseNodes:

       >>> test = "/company/{name:[a-z][A-Z]{10}[0-9]*}/bla/bla/{dept}"
       >>> list(parse_dynamic(test))
       ['/company/',
        <tokamak.types.DynamicParseNode at 0x7f82e1b3a280>,
        '/bla/bla/',
        <tokamak.types.DynamicParseNode at 0x7f82e1b3a220>]
    """
    stack: typing.Deque[int] = deque()
    regex_stack: typing.Deque[int] = deque()
    inside_dyn = False
    has_regex = False
    static: typing.List[str] = []
    last_dyn_node_idx = None

    # parse each char for `{` followed by `:` followed by `}`
    # append to a static set of chars if we're _not_ inside one of these dynamic chunks.
    for idx, char in enumerate(path):
        if char == ParamToken.LEFT_BRACE.value:
            if last_dyn_node_idx is not None and last_dyn_node_idx == idx - 1:
                raise ValueError(
                    "Dynamic nodes must have at least one character between them"
                )
            inside_dyn = True
            if has_regex:
                regex_stack.append(idx)
            else:
                # start of a dynamic param, yield current static if present
                if static:
                    yield "".join(static)
                    static = []

                assert (
                    len(stack) == 0
                ), "Found nested dynamic chunk start: `{` with no matching `}`"
                stack.append(idx)

        elif char == ParamToken.COLON.value:
            if not has_regex:
                has_regex = True
                assert len(stack) == 1, "Found colon without named parameter"
                stack.append(idx)

        elif char == ParamToken.RIGHT_BRACE.value:
            if has_regex and regex_stack:
                regex_stack.pop()
                # advance the parser: assumes a curly brace pair inside a regex
                continue

            if not regex_stack:
                assert (
                    0 < len(stack) <= 2
                ), "Unbalanced curly braces: found right-hand side without left"
                start = stack.pop()
                colon = idx
                end = idx
                regex = None
                if has_regex:
                    colon = start
                    start = stack.pop()
                    regex = path[colon + 1 : end]

                has_regex = False
                raw = path[start : idx + 1]
                name = path[start + 1 : colon]
                yield DynamicParseNode(raw, name, regex=regex)
                last_dyn_node_idx = idx
                inside_dyn = False

        elif not inside_dyn:
            # accumulate static values
            static.append(char)

    if static:
        yield "".join(static)

    if stack or regex_stack:
        logger.warning("Incomplete dynamic parse: output orphaned")
