#  Manos
#  Copyright (C) 2023-2024, Henry Stratmann III
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 3 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

# This implementation is derived from: https://github.com/rspeer/ordered-set

import itertools as it
import typing
import sys

from typing import (
    Dict,
    List,
    Iterable,
    Iterator,
    MutableSet,
    AbstractSet,
    Sequence,
    TypeVar,
    Union,
    Optional,
    overload,
)

T = TypeVar("T")

# SetLike[T] is either a set of elements of type T, or a sequence, which
# we will convert to an OrderedSet by adding its elements in order.
SetLike = Union[AbstractSet[T], Sequence[T]]
OrderedSetInitializer = Union[AbstractSet[T], Sequence[T], Iterable[T]]

class OrderedSet(MutableSet[T], Sequence[T]):
    def __init__(self, initial: Optional[OrderedSetInitializer[T]] = None):
        self.items: List[T] = []
        self.map: Dict[T, int] = {}
        if initial is not None:
            # In terms of duck-typing, the default __ior__ is compatible with
            # the types we use, but it doesn't expect all the types we
            # support as values for `initial`.
            self |= initial  # type: ignore

    # Returns the number of unique elements in the ordered set.
    def __len__(self) -> int:
        return len(self.items)

    # Get the item at a given index.
    @overload
    def __getitem__(self, index: int) -> T:
        return self.items[index]

    # If `index` is a slice, you will get back that slice of items, as a new OrderedSet.
    @overload
    def __getitem__(self, index: slice) -> "OrderedSet[T]":
        ...

    # Concrete implementation.
    # Disable type checking because the overloads provide the typed signatures.
    @typing.no_type_check
    def __getitem__(self, index):
        result = self.items[index]
        if isinstance(result, list):
            return self.__class__(result)
        else:
            return result

    # Return a shallow copy of this object.
    def copy(self) -> "OrderedSet[T]":
        return self.__class__(self)

    def __contains__(self, key: object) -> bool:
        return key in self.map

    def append(self, key: T) -> int:
        if key not in self.map:
            self.map[key] = len(self.items)
            self.items.append(key)
        return self.map[key]

    # Add `key` as an item to this OrderedSet.
    def add(self, key: T) -> None:
        self.append(key)

    # Get the index of a given entry, raising an IndexError if it's not present.
    def index(self, value: T, start: int = 0, stop: int = sys.maxsize) -> int:
        if start == 0 and stop == sys.maxsize:
            return self.map[value]
        return self.items.index(value, start, stop)

    # Remove and return item at index (default last). Raise an exception if absent.
    def pop(self, index: int = -1) -> T:
        if not self.items:
            raise KeyError("Set is empty")
        elem = self.items[index]
        del self.items[index]
        del self.map[elem]
        return elem

    # Remove an element. Do not raise an exception if absent.
    def discard(self, key: T) -> None:
        if key in self:
            i = self.map[key]
            del self.items[i]
            del self.map[key]
            for k, v in self.map.items():
                if v >= i:
                    self.map[k] = v - 1

    # Remove all items from this OrderedSet.
    def clear(self) -> None:
        del self.items[:]
        self.map.clear()

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __reversed__(self) -> Iterator[T]:
        return reversed(self.items)

    def __repr__(self) -> str:
        if not self:
            return f"{self.__class__.__name__}()"
        return f"{self.__class__.__name__}({list(self)!r})"

    # Returns true if the containers have the same items.
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Sequence):
            # Check that this OrderedSet contains the same elements, in the
            # same order, as the other object.
            return list(self) == list(other)
        try:
            other_as_set = set(other) # type: ignore
        except TypeError:
            # If `other` can't be converted into a set, it's not equal.
            return False
        else:
            return True if set(self) == other_as_set else False

    # Combines all unique items.
    def union(self, *sets: SetLike[T]) -> "OrderedSet[T]":
        cls: type = OrderedSet
        if isinstance(self, OrderedSet):
            cls = self.__class__
        containers = map(list, it.chain([self], sets))
        items = it.chain.from_iterable(containers)
        return cls(items)

    # Returns elements in common between all sets. Order is defined only by the first set.
    def intersection(self, *sets: SetLike[T]) -> "OrderedSet[T]":
        cls: type = OrderedSet
        items: OrderedSetInitializer[T] = self
        if isinstance(self, OrderedSet):
            cls = self.__class__
        if sets:
            common = set.intersection(*map(set, sets))
            items = (item for item in self if item in common)
        return cls(items)

    # Returns all elements that are in this set but not the others.
    def difference(self, *sets: SetLike[T]) -> "OrderedSet[T]":
        cls = self.__class__
        items: OrderedSetInitializer[T] = self
        if sets:
            other = set.union(*map(set, sets))
            items = (item for item in self if item not in other)
        return cls(items)
