"""Errors the guard commands report to the user."""

from __future__ import annotations


class GuardError(Exception):
    """A refusal: the command ran but its precondition failed (exit 1)."""


class NotARepo(GuardError):
    """The working directory is not inside a git repository (exit 2)."""
