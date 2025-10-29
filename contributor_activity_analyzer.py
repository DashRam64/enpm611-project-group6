from collections import defaultdict
from typing import List, Dict
import matplotlib.pyplot as plt
from data_loader import DataLoader
from model import Issue, State

class ContributorActivityAnalyzer:

    def run(self):
        issues: List[Issue] = DataLoader().get_issues()

        #console output
        self.printActiveIssuesPerContributor(issues)
        self.printIssueTypeDistributionPerContributor(issues)
        self.printContributorSummary(issues)

        # Plot charts
        self.plot_top_contributors_by_active_issues(issues)
        self.plot_issue_type_distribution_per_contributor(issues)

    @staticmethod
    def get_active_issues_count_per_contributor(issues: List[Issue]) -> Dict[str, int]:
        active_issues_count = defaultdict(int)
        for issue in issues:
            if issue.state == State.open:
                for contributor in issue.assignees:
                    active_issues_count[contributor["login"]] += 1
        return dict(active_issues_count)

    @staticmethod
    def get_issue_type_distribution_per_contributor(issues: List[Issue]) -> Dict[str, Dict[str, int]]:
        contributor_distribution = defaultdict(lambda: defaultdict(int))
        for issue in issues:
            kinds = [label.split('/')[1] for label in issue.labels if label.startswith("kind/")]
            for contributor in issue.assignees:
                for kind in kinds:
                    contributor_distribution[contributor["login"]][kind] += 1
        return {contrib: dict(dist) for contrib, dist in contributor_distribution.items()}
    
    @staticmethod
    def get_contributor_summary(contributor_name: str, issues: List[Issue]) -> Dict:
        active_counts = ContributorActivityAnalyzer.get_active_issues_count_per_contributor(issues)
        type_distribution = ContributorActivityAnalyzer.get_issue_type_distribution_per_contributor(issues)

        summary = {
            "active_issues": active_counts.get(contributor_name, 0),
            "issue_type_distribution": type_distribution.get(contributor_name, {})
        }
        return summary

    @staticmethod
    def plot_top_contributors_by_active_issues(issues: List[Issue]):
        counts = ContributorActivityAnalyzer.get_active_issues_count_per_contributor(issues)
        contributors = list(counts.keys())
        active_counts = list(counts.values())
        sorted_data = sorted(zip(contributors, active_counts), key=lambda x: x[1], reverse=True)
        sorted_contributors, sorted_counts = zip(*sorted_data)
        plt.figure(figsize=(10, 6))
        plt.barh(sorted_contributors, sorted_counts, color="skyblue")
        plt.xlabel("Number of Active Issues")
        plt.title("Active Issues per Contributor")
        plt.gca().invert_yaxis()
        plt.show()

    @staticmethod
    def plot_issue_type_distribution_per_contributor(issues: List[Issue]):
        distribution = ContributorActivityAnalyzer.get_issue_type_distribution_per_contributor(issues)
        contributors = list(distribution.keys())
        kinds = set(kind for dist in distribution.values() for kind in dist)
        kinds = sorted(kinds)
        data = {kind: [] for kind in kinds}
        for contributor in contributors:
            for kind in kinds:
                data[kind].append(distribution[contributor].get(kind, 0))
        plt.figure(figsize=(12, 6))
        bottom = [0] * len(contributors)
        colors = plt.cm.tab20.colors
        for i, kind in enumerate(kinds):
            plt.barh(contributors, data[kind], left=bottom, color=colors[i % len(colors)], label=kind)
            bottom = [bottom[j] + data[kind][j] for j in range(len(bottom))]
        plt.xlabel("Number of Issues")
        plt.ylabel("Contributors")
        plt.title("Issue Distribution by Kind per Contributor")
        plt.legend(title="Issue Kind")
        plt.gca().invert_yaxis()
        plt.show()

  
    def printActiveIssuesPerContributor(self,issues):
        print("Active Issues per Contributor:")
        active_counts = self.get_active_issues_count_per_contributor(issues)
        for contributor, count in active_counts.items():
            print(f"{contributor}: {count}")

    def printIssueTypeDistributionPerContributor(self,issues):
        print("\nIssue Type Distribution per Contributor:")
        issue_distribution = self.get_issue_type_distribution_per_contributor(issues)
        for contributor, dist in issue_distribution.items():
            print(f"{contributor}: {dist}")
        
    def printContributorSummary(self,issues):
        while True:
            contributor_input = input("\nEnter a contributor name to view summary (or 'q' to continue): ").strip()
            if contributor_input.lower() == 'q':
                break
            all_contributors = ContributorActivityAnalyzer.get_issue_type_distribution_per_contributor(issues).keys()
            contributors_lower_map = {c.lower(): c for c in all_contributors}
            contributor_name = contributors_lower_map.get(contributor_input.lower())
            if not contributor_name:
                print(f"No data found for contributor '{contributor_input}'.")
                continue
            summary = self.get_contributor_summary(contributor_name, issues)
            print(f"\nSummary for {contributor_name}:")
            print(f"Active Issues: {summary['active_issues']}")
            print("Issue Type Distribution:")
            for kind, count in summary["issue_type_distribution"].items():
                print(f"  {kind}: {count}")