"""
CLI Interface for the Adaptive Testing System
Provides a rich terminal-based testing experience.

Author: [Candidate Name]
AI-Assisted: Rich library formatting patterns referenced from documentation.
Core flow logic is manual implementation.
"""

import sys
import time
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich.layout import Layout
from rich.markdown import Markdown
from config import Config

# Set up logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_session.log'),
        logging.StreamHandler() if Config.LOG_LEVEL == "DEBUG" else logging.NullHandler()
    ]
)

console = Console()


def display_welcome():
    """Display welcome screen and instructions."""
    welcome_text = """
# 🧠 AI-Powered Adaptive Cognitive Assessment

Welcome to the Adaptive Testing System!

## How it works:
- You'll be asked a series of cognitive questions
- The system **adapts** to your performance in real-time
- Strong performance → harder questions
- Struggling? → the system adjusts to find your level
- Multiple cognitive categories are tested

## Categories tested:
- Logical Reasoning
- Pattern Recognition
- Verbal Reasoning
- Numerical Reasoning
- Spatial Reasoning
- Working Memory
- Critical Thinking

## Tips:
- Read each question carefully
- Answer at your own pace (but quicker = bonus points!)
- Don't worry about mistakes — they help calibrate the test

---
    """
    console.print(Markdown(welcome_text))


def display_question(question_data: dict):
    """Display a question with formatting."""
    console.print()
    console.print(f"[bold cyan]━━━ Question {question_data['question_number']}/{question_data['total_questions']} ━━━[/bold cyan]")
    console.print(f"[dim]Category: {question_data['category']} | Difficulty: {question_data['difficulty']}[/dim]")
    console.print(f"[dim]Score: {question_data['current_score']} | Ability: {question_data['estimated_ability']}/5.0[/dim]")
    console.print()

    # Show adaptive explanation (bonus feature)
    console.print(Panel(
        question_data['adaptive_explanation'],
        title="🤖 Why this question?",
        style="dim italic",
        border_style="blue"
    ))

    # Show strategy
    console.print(f"[dim]{question_data['strategy']}[/dim]")
    console.print()

    # Display question
    console.print(Panel(
        question_data['text'],
        title="Question",
        border_style="yellow",
        padding=(1, 2)
    ))

    # Display options
    for i, option in enumerate(question_data['options']):
        console.print(f"  [bold]{i + 1}.[/bold] {option}")
    console.print()


def display_result(result: dict):
    """Display the result of an answer."""
    if result['is_correct']:
        console.print(Panel(
            f"[bold green]✓ CORRECT![/bold green]\n\n"
            f"Score earned: +{result['score_earned']}\n"
            f"Time: {result['time_taken']}s\n\n"
            f"{result['feedback']}",
            border_style="green",
            title="Result"
        ))
    else:
        console.print(Panel(
            f"[bold red]✗ INCORRECT[/bold red]\n\n"
            f"Correct answer: {result['correct_answer_text']}\n"
            f"Time: {result['time_taken']}s\n\n"
            f"{result['feedback']}",
            border_style="red",
            title="Result"
        ))

    # Show current stats
    stats = result['current_stats']
    console.print(f"[dim]Accuracy: {stats['accuracy']}% | "
                  f"Ability: {stats['estimated_ability']}/5.0 | "
                  f"Total Score: {result['total_score']}[/dim]")

    if result.get('difficulty_explanation'):
        console.print(f"\n[dim italic]{result['difficulty_explanation']}[/dim italic]")


def display_final_results(results: dict):
    """Display comprehensive final results."""
    profile = results['profile']
    summary = profile['summary']

    console.print()
    console.print("=" * 60)
    console.print("[bold magenta]🏆 TEST COMPLETE — COGNITIVE PROFILE[/bold magenta]")
    console.print("=" * 60)

    # Summary panel
    console.print(Panel(
        f"[bold]{summary['performance_level']}[/bold]\n"
        f"{summary['description']}\n\n"
        f"Total Score: {summary['total_score']}\n"
        f"Accuracy: {summary['accuracy_percentage']}%\n"
        f"Estimated Percentile: {summary['estimated_percentile']}%",
        title="📊 Overall Assessment",
        border_style="magenta"
    ))

    # Category breakdown table
    cat_analysis = profile.get('category_analysis', {})
    if cat_analysis:
        table = Table(title="📋 Category Performance", show_header=True)
        table.add_column("Category", style="cyan")
        table.add_column("Questions", justify="center")
        table.add_column("Accuracy", justify="center")
        table.add_column("Weighted Score", justify="center")
        table.add_column("Level", justify="center")

        for cat_key, data in cat_analysis.items():
            level_style = "green" if data['level'] == "Strong" else "yellow" if data['level'] == "Moderate" else "red"
            table.add_row(
                data['name'],
                str(data['questions_attempted']),
                f"{data['accuracy']}%",
                f"{data['weighted_score']:.1f}",
                f"[{level_style}]{data['level']}[/{level_style}]"
            )
        console.print(table)

    # Difficulty progression
    diff_prog = profile.get('difficulty_progression', {})
    if diff_prog.get('progression'):
        console.print(f"\n[bold]📈 Difficulty Trend:[/bold] {diff_prog.get('trend', 'N/A')}")

        # Visual progression
        prog_visual = ""
        for step in diff_prog['progression']:
            marker = "✓" if step['correct'] else "✗"
            level = "▁▂▃▄▅"[min(step['difficulty'] - 1, 4)]
            color = "green" if step['correct'] else "red"
            prog_visual += f"[{color}]{level}{marker}[/{color}] "
        console.print(f"  Progression: {prog_visual}")

    # Strengths and weaknesses
    strengths = profile.get('strengths', [])
    weaknesses = profile.get('weaknesses', [])

    if strengths:
        console.print("\n[bold green]💪 Strengths:[/bold green]")
        for s in strengths:
            console.print(f"  • {s}")

    if weaknesses:
        console.print("\n[bold yellow]🎯 Areas for Growth:[/bold yellow]")
        for w in weaknesses:
            console.print(f"  • {w}")

    # Response patterns
    patterns = profile.get('response_patterns', {})
    if patterns:
        console.print("\n[bold]⏱️ Response Patterns:[/bold]")
        console.print(f"  Average time: {patterns.get('average_response_time', 'N/A')}s")
        if 'speed_accuracy_note' in patterns:
            console.print(f"  {patterns['speed_accuracy_note']}")

    # Narrative profile
    narrative = profile.get('narrative_profile', '')
    if narrative:
        console.print(Panel(
            narrative,
            title="📝 Detailed Cognitive Profile",
            border_style="blue",
            padding=(1, 2)
        ))

    # Adaptive journey summary
    journey = profile.get('adaptive_journey', [])
    if journey and len(journey) > 0:
        console.print("\n[bold]🔄 Adaptive Journey:[/bold]")
        for step in journey[:5]:  # Show first 5
            console.print(f"  Step {step['step']}: {step['question_selected']} "
                          f"(Difficulty: {step['target_difficulty']})")
            console.print(f"    [dim]{step['reasoning_summary']}[/dim]")

    # Decision log
    if results.get('decision_log'):
        show_log = Prompt.ask("\nView full adaptive decision log?", choices=["y", "n"], default="n")
        if show_log == "y":
            console.print(Panel(
                results['decision_log'],
                title="📋 Full Decision Log",
                border_style="dim"
            ))


def run_cli_test():
    """Main CLI test runner."""
    from test_runner import TestSession

    # Validate config
    warnings = Config.validate()
    for w in warnings:
        console.print(f"[yellow]⚠ {w}[/yellow]")

    display_welcome()

    # Get user info
    user_id = Prompt.ask("Enter your name/ID", default="user")
    num_questions = IntPrompt.ask(
        "Number of questions",
        default=Config.MAX_QUESTIONS,
    )
    num_questions = max(Config.MIN_QUESTIONS, min(num_questions, 20))

    console.print(f"\n[bold]Starting test with {num_questions} questions...[/bold]")
    console.print("[dim]Press Ctrl+C at any time to end early.[/dim]\n")
    time.sleep(1)

    # Create session
    session = TestSession(user_id=user_id, max_questions=num_questions)

    try:
        while True:
            # Get next question
            question_data = session.get_next_question()
            if question_data is None:
                break

            display_question(question_data)

            # Get answer
            while True:
                try:
                    answer = IntPrompt.ask(
                        "Your answer (1-4)",
                    )
                    if 1 <= answer <= len(question_data['options']):
                        break
                    console.print("[red]Please enter a valid option number.[/red]")
                except ValueError:
                    console.print("[red]Please enter a number.[/red]")

            # Optional confidence
            confidence = Prompt.ask(
                "Confidence level",
                choices=["very_low", "low", "medium", "high", "very_high"],
                default="medium"
            )

            # Submit answer (0-indexed)
            result = session.submit_answer(answer - 1, confidence=confidence)
            display_result(result)

            if result['is_test_complete']:
                break

            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Test ended early by user.[/yellow]")

    # Show results
    console.print("\n[bold]Generating your cognitive profile...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing results...", total=None)
        results = session.get_final_results()
        progress.update(task, description="Complete!")

    display_final_results(results)

    console.print("\n[bold green]Thank you for completing the assessment![/bold green]")


if __name__ == "__main__":
    run_cli_test()