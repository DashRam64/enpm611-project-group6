import json
from typing import List
from datetime import datetime, timezone

import config
from model import Issue

# Store issues as singleton to avoid reloads
_ISSUES: List[Issue] = None


class DataLoader:
    """
    Loads the issue data into a runtime object and applies filters
    based on config.START_DATE / END_DATE / LABEL_FILTER / STATE_FILTER.
    """

    def __init__(self):
        """
        Constructor
        """
        self.data_path: str = config.get_parameter("ENPM611_PROJECT_DATA_PATH")

    def get_issues(self) -> List[Issue]:
        """
        This should be invoked by other parts of the application to get access
        to the issues in the data file.

        - Loads all issues once into _ISSUES.
        - Returns a filtered view based on config filters.
        """
        global _ISSUES
        if _ISSUES is None:
            _ISSUES = self._load()
            print(f"Loaded {len(_ISSUES)} issues from {self.data_path}.")

        filtered = self._apply_filters(_ISSUES)
        print(
            f"Filters applied -> {len(filtered)} issues remain "
            f"(start={config.START_DATE}, end={config.END_DATE}, "
            f"label={config.LABEL_FILTER}, state={config.STATE_FILTER})"
        )
        return filtered

    def _load(self) -> List[Issue]:
        """
        Loads the issues into memory (unfiltered).
        """
        with open(self.data_path, "r") as fin:
            return [Issue(i) for i in json.load(fin)]

    def _apply_filters(self, issues: List[Issue]) -> List[Issue]:
        """
        Applies date, label, and state filters from config to the full issue list.
        Does NOT mutate the global _ISSUES.
        """
        start_dt = self._normalize_datetime(config.START_DATE)
        end_dt = self._normalize_datetime(config.END_DATE)
        label_filter = config.LABEL_FILTER
        state_filter = config.STATE_FILTER

        filtered: List[Issue] = []

        for issue in issues:
            # --- Get created date from the Issue object ---
            # Try a couple of common attribute names just in case the model uses a different one
            raw_created = None
            for attr in ("created_at", "created", "createdAt", "created_date", "createdDate"):
                raw_created = getattr(issue, attr, None)
                if raw_created is not None:
                    break

            created_dt: datetime | None = None

            # Normalize created_at into a datetime if possible
            if isinstance(raw_created, datetime):
                created_dt = raw_created  # normalized below
            elif isinstance(raw_created, str):
                try:
                    # Handle GitHub-style "YYYY-MM-DDTHH:MM:SSZ"
                    if raw_created.endswith("Z"):
                        created_dt = datetime.fromisoformat(
                            raw_created.replace("Z", "+00:00")
                        )
                    else:
                        created_dt = datetime.fromisoformat(raw_created)
                except Exception:
                    created_dt = None
            created_dt = self._normalize_datetime(created_dt)

            # If there is ANY date filter and we couldn't parse this issue's date,
            # drop this issue (otherwise the filter appears to do nothing).
            if (start_dt or end_dt) and created_dt is None:
                continue

            # --- Date filters (only if we were able to parse a date) ---
            if start_dt and created_dt and created_dt < start_dt:
                continue
            if end_dt and created_dt and created_dt > end_dt:
                continue

            # --- Label filter ---
            if label_filter:
                labels = getattr(issue, "labels", None)
                if not labels or label_filter not in labels:
                    continue

            # --- State filter ---
            if state_filter:
                state = getattr(issue, "state", None)
                state_value = (
                    state.value if hasattr(state, "value") else str(state).lower()
                )
                state_filter_value = (
                    state_filter.value
                    if hasattr(state_filter, "value")
                    else str(state_filter).lower()
                )
                if state_value != state_filter_value:
                    continue

            filtered.append(issue)

        return filtered

    @staticmethod
    def _normalize_datetime(dt: datetime | None) -> datetime | None:
        """
        Converts all datetimes to timezone-aware UTC so comparisons don't fail
        (user inputs are typically naive, dataset timestamps are often UTC+offset).
        """
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


if __name__ == "__main__":
    # Run the loader for testing
    issues = DataLoader().get_issues()
    print(f"[Test] After filtering, {len(issues)} issues remain.")
