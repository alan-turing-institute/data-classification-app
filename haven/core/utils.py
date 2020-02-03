from collections import defaultdict


class TextTable:
    '''
    Utility class for parsing a variable-whitespace-delimited table into a two-dimensional
    dict.

    For example, the following:

    table = Table("""
             Col1 Col2
        Row1    A    B
        Row2    A    A
        Row3    C    .
    """)
    parsed = table.as_dict()

    will give the result:

    {
        'Row1': {
            'Col1': 'A',
            'Col2': 'B',
        },
        'Row2': {
            'Col1': 'A',
            'Col2': 'A',
        },
        'Row3': {
            'Col1': 'C',
            'Col2': '.',
        },
    }

    Row and column headers must be valid identifiers (according to str.isidentifier()), or they
    will be ignored. Similarly, the `ignore` attribute can be used to add additional non-functional
    information. Finally, the `abbreviations` attribute can be used to make the definition smaller,
    e.g.

    table = Table(
        definition="""
                 | C1 Col2 | Notes
            R1   |  A    . | This one's special
            Row2 |  A    Y |
            -----+---------+-------------------
            Row3 |  .    . |
        """,
        abbreviations={'R1': 'Row1', 'C1': 'Col1'},
        ignore=['Notes'],
    )
    table.as_dict()

    will give the result:

    {
        'Row1': {
            'Col1': 'A',
            'Col2': '.',
        },
        'Row2': {
            'Col1': 'A',
            'Col2': 'Y',
        },
        'Row3': {
            'Col1': '.',
            'Col2': '.',
        },
    }
    Note that while generally the definition is most readable in a fixed-width format, this is
    not enforced, e.g. the following gives the same result

    table = Table("""
         Col1 Col2
        Row1 A .
        Row2 A  Y
        Row3 .   .
    """)
    '''
    def __init__(self, definition, abbreviations=None, ignore=None, default=None):
        super().__init__()
        self.definition = definition
        self.abbreviations = abbreviations or {}
        self.abbreviations_inverse = {v: k for k, v in self.abbreviations.items()}
        self.ignore = ignore or []
        self.default = default
        self._as_dict = None

    def as_dict(self):
        if self._as_dict is None:
            self._as_dict = {}
            lines = self.definition.strip().splitlines()
            headers = lines[0].split()
            for line in lines[1:]:
                row = line.split()
                key = row[0]
                if key in self.ignore:
                    continue
                if not key.isidentifier():
                    continue
                key = self.abbreviations.get(key, key)
                self._as_dict[key] = defaultdict(self.default)
                for i, cell in enumerate(row[1:]):
                    key2 = headers[i]
                    if key2 in self.ignore:
                        continue
                    if not key2.isidentifier():
                        continue
                    key2 = self.abbreviations.get(key2, key2)
                    cell = self.coerce(cell)
                    self._as_dict[key][key2] = cell
        return self._as_dict

    def coerce(self, value):
        return value


class BooleanTextTable(TextTable):
    '''
    Sub-class of TextTable which coerces values into booleans.

    By default, the only value considered true is 'Y'. This can be over-ridden with a list of valid
    values for the `truthy` attribute

    For example, the following:

    table = Table("""
             Col1 Col2
        Row1    Y    .
        Row2    Y    Y
        Row3    .    .
    """)
    parsed = table.as_dict()

    will give the result:

    {
        'Row1': {
            'Col1': True,
            'Col2': False,
        },
        'Row2': {
            'Col1': True,
            'Col2': True,
        },
        'Row3': {
            'Col1': False,
            'Col2': False,
        },
    }

    '''
    def __init__(self, *args, truthy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.truthy = truthy or ['Y']

    def coerce(self, value):
        return value in self.truthy
