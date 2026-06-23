#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.client import ConcurClient, ConcurError
from src.browser_client import ConcurBrowserClient


def run_tests():
    # Load .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description="SAP Concur API & Browser Access Tool")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommands")

    # Command: api-test
    subparsers.add_parser("api-test", help="Run the API client test suite")

    # Command: login
    subparsers.add_parser("login", help="Launch a headed browser for manual authentication and save session state")

    # Command: check-session
    subparsers.add_parser("check-session", help="Check whether the currently saved browser session state is valid and active")

    # Command: query
    subparsers.add_parser("query", help="Query and list current reports and available receipts via browser automation")

    # Command: create-report
    p_create = subparsers.add_parser("create-report", help="Create a draft expense report using browser automation")
    p_create.add_argument("--name", type=str, help="Name of report to create")
    p_create.add_argument("--purpose", type=str, help="Business purpose of report to create")
    p_create.add_argument("--comment", type=str, help="Additional comment for report to create")
    p_create.add_argument("--headed", action="store_true", help="Run browser visibly (headed) rather than headlessly")

    # Command: delete-report
    p_del = subparsers.add_parser("delete-report", help="Delete an expense report by name using browser automation")
    p_del.add_argument("report_name", type=str, help="Name of report to delete")

    # Command: delete-all-reports
    subparsers.add_parser("delete-all-reports", help="Delete all draft expense reports via browser")

    # Command: delete-all-receipts
    subparsers.add_parser("delete-all-receipts", help="Delete all available receipts via browser")

    # Command: nuke
    subparsers.add_parser("nuke", help="Delete all draft expense reports AND all available receipts via browser")

    # Command: list-old-reports
    p_list_old = subparsers.add_parser("list-old-reports", help="Query and list historical/old expense reports")
    p_list_old.add_argument("--filter-view", type=str, default="Last 90 Days", help="Dropdown filter (default: 'Last 90 Days')")

    # Command: report-details
    p_rep_det = subparsers.add_parser("report-details", help="Get detailed view of an expense report by name")
    p_rep_det.add_argument("report_name", type=str, help="Name of the expense report")
    p_rep_det.add_argument("--filter-view", type=str, default="Last 90 Days", help="Dropdown filter to look inside (default: 'Last 90 Days')")

    # Command: list-cards
    p_list_cards = subparsers.add_parser("list-cards", help="Query and list credit card transactions")
    p_list_cards.add_argument("--filter-view", type=str, default="All Corporate and Personal Cards", help="Filter view for cards (default: 'All Corporate and Personal Cards')")

    # Command: card-details
    p_card_det = subparsers.add_parser("card-details", help="Get detailed view of a card transaction by merchant or ID")
    p_card_det.add_argument("merchant_or_id", type=str, help="Merchant name or transaction ID")
    p_card_det.add_argument("--filter-view", type=str, default="All Corporate and Personal Cards", help="Filter view for cards (default: 'All Corporate and Personal Cards')")

    # Command: add-delegate
    p_add_del = subparsers.add_parser("add-delegate", help="Add a new expense delegate by name or email")
    p_add_del.add_argument("name_or_email", type=str, help="Name or email of delegate")
    p_add_del.add_argument("--delegate-perms", nargs="+", default=["prepare"], help="Permissions: prepare, submit, approve")

    # Command: remove-delegate
    p_rem_del = subparsers.add_parser("remove-delegate", help="Remove an expense delegate by name or email")
    p_rem_del.add_argument("name_or_email", type=str, help="Name or email of delegate")

    # Command: reconcile
    p_recon = subparsers.add_parser("reconcile", help="Reconcile transactions of an expense report by name")
    p_recon.add_argument("report_name", type=str, help="Name of draft report to reconcile")
    p_recon.add_argument("--reconcile-rules", type=str, help="Path to a JSON file containing reconciliation rules")
    p_recon.add_argument("--submit", action="store_true", help="Submit the report after reconciling (default: False, review-only)")

    # Command: attach-receipt
    p_attach = subparsers.add_parser("attach-receipt", help="Attach a receipt file to a transaction in a report")
    p_attach.add_argument("report_name", type=str, help="Name of report containing the transaction")
    p_attach.add_argument("--merchant", type=str, required=True, help="Merchant name or transaction ID to match receipt against")
    p_attach.add_argument("--receipt-path", type=str, required=True, help="Local file path of the receipt")

    args = parser.parse_args()

    # ----------------------------------------------------
    # Flow A: Live API Client Tester
    # ----------------------------------------------------
    if args.command == "api-test":
        client_id = os.getenv("CONCUR_CLIENT_ID")
        client_secret = os.getenv("CONCUR_CLIENT_SECRET")
        token_url = os.getenv("CONCUR_TOKEN_URL", "https://us.api.concursolutions.com/oauth2/v0/token")
        base_url = os.getenv("CONCUR_BASE_URL", "https://us.api.concursolutions.com")
        user_login_id = os.getenv("CONCUR_USER_LOGIN_ID")

        print("=" * 60)
        print("           SAP Concur API Access Tester Script")
        print("=" * 60)

        missing_vars = []
        if not client_id or client_id == "your_client_id_here":
            missing_vars.append("CONCUR_CLIENT_ID")
        if not client_secret or client_secret == "your_client_secret_here":
            missing_vars.append("CONCUR_CLIENT_SECRET")
        if not user_login_id or user_login_id == "user@example.com":
            missing_vars.append("CONCUR_USER_LOGIN_ID")

        if missing_vars:
            print("\n[!] Configuration Missing.")
            print("Please configure your credentials in the '.env' file.")
            print("Required variables missing:")
            for var in missing_vars:
                print(f"  - {var}")
            print("\nYou can copy '.env.example' to '.env' and update it:")
            print("  cp .env.example .env")
            print("=" * 60)
            sys.exit(1)

        print(f"[*] Base URL:  {base_url}")
        print(f"[*] Token URL: {token_url}")
        print(f"[*] Test User: {user_login_id}")
        print(f"[*] Client ID: {client_id[:6]}... (truncated)")
        print("-" * 60)

        try:
            client = ConcurClient(
                client_id=client_id,
                client_secret=client_secret,
                token_url=token_url,
                base_url=base_url
            )

            print("\n[Phase 1] Attempting authentication...")
            token = client.get_token()
            print("[SUCCESS] Authentication succeeded!")
            print(f"          Access token acquired (starts with: '{token[:12]}...')")

            print("\n[Phase 2] Attempting to list existing reports...")
            reports = client.list_reports(user_login_id=user_login_id, limit=5)
            print("[SUCCESS] Successfully connected to report list API!")
            print(f"          Retrieved {len(reports)} recent report(s):")
            
            for idx, report in enumerate(reports, 1):
                report_name_val = report.get("Name", "Unnamed Report")
                report_id = report.get("ReportID") or report.get("ID") or "N/A"
                report_status = report.get("ReportStatus") or report.get("ApprovalStatus") or "N/A"
                total = report.get("Total", 0.0)
                currency = report.get("CurrencyCode", "")
                print(f"            {idx}. [{report_id}] {report_name_val} - Status: {report_status} ({total} {currency})")

            print("\n[Phase 3] Attempting to create draft report...")
            report_name_val = f"API Test Draft {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            purpose = "Validating programmatic creation of draft reports"
            comment = "Created automatically via SAP Concur Python API Access Tester"

            created_report = client.create_draft_report(
                user_login_id=user_login_id,
                name=report_name_val,
                purpose=purpose,
                comment=comment
            )

            print("[SUCCESS] Programmatic report creation succeeded!")
            print(f"          New Report Name: {created_report.get('Name')}")
            print(f"          Report ID:       {created_report.get('ReportID') or created_report.get('ID')}")
            print(f"          Status:          {created_report.get('ReportStatus', 'Draft / Not Submitted')}")
            print("-" * 60)
            print("\n[SUMMARY] All API tests passed! You have full read/write access.")

        except ConcurError as e:
            print(f"\n[ERROR] An API error occurred during testing:")
            print(f"        {str(e)}")
            print("-" * 60)
            sys.exit(1)
        except Exception as e:
            print(f"\n[UNEXPECTED ERROR] An unexpected error occurred:")
            print(f"        {str(e)}")
            print("-" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow B: Browser Manual Login Session Save
    # ----------------------------------------------------
    elif args.command == "login":
        print("=" * 60)
        print("       SAP Concur Browser Authentication Session Setup")
        print("=" * 60)
        
        try:
            browser_client = ConcurBrowserClient()
            browser_client.run_headed_login()
            print("\n[SUCCESS] Setup complete. You can now run browser-based automations.")
            print("To run the draft creator, use: python3 src/cli.py create-report")
        except Exception as e:
            print(f"\n[ERROR] Failed to run manual login setup: {str(e)}")
            sys.exit(1)

    # ----------------------------------------------------
    # Flow B.2: Browser Check Session Validity
    # ----------------------------------------------------
    elif args.command == "check-session":
        print("=" * 60)
        print("     SAP Concur Browser Session Status Check")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            result = browser_client.check_session_validity(headless=True)
            if result.get("authenticated"):
                print(f"\n[SUCCESS] Authentication is active and valid!")
                print(f"          Detail: {result.get('reason')}")
                print("=" * 60)
            else:
                print(f"\n[EXPIRED/NOT FOUND] Authentication is NOT valid.")
                print(f"                    Detail: {result.get('reason')}")
                print("=" * 60)
                sys.exit(2)
        except Exception as e:
            print(f"\n[ERROR] Failed to execute session status check: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow C: Browser Query (List Reports + List Receipts)
    # ----------------------------------------------------
    elif args.command == "query":
        print("=" * 60)
        print("     SAP Concur Browser-Based Expense & Receipt Query")
        print("=" * 60)
        
        try:
            browser_client = ConcurBrowserClient()
            
            # Query reports
            print("\n[*] Querying active expense reports...")
            reports = browser_client.list_reports(headless=True)
            print(f"[SUCCESS] Discovered {len(reports)} expense report(s):")
            for idx, r in enumerate(reports, 1):
                print(f"  {idx}. {r.get('name')} (Purpose: {r.get('purpose', 'None')})")

            # Query available receipts
            print("\n[*] Querying available receipts gallery...")
            receipts = browser_client.list_available_receipts(headless=True)
            print(f"[SUCCESS] Discovered {len(receipts)} uploaded receipt(s):")
            for idx, name in enumerate(receipts, 1):
                print(f"  {idx}. {name}")
                
            print("\n" + "=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Browser query failed: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow D: Browser Draft Report Creation (Headless/Headed)
    # ----------------------------------------------------
    elif args.command == "create-report":
        print("=" * 60)
        print("     SAP Concur Browser-Based Draft Report Creation")
        print("=" * 60)
        
        headless = not args.headed
        report_name_val = args.name or f"Browser Test Draft {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        purpose = args.purpose or "Validating browser-based creation of draft reports"
        comment = args.comment or "Created automatically via SAP Concur Python Playwright Tester"

        try:
            browser_client = ConcurBrowserClient()
            result = browser_client.create_draft_report(
                name=report_name_val,
                purpose=purpose,
                comment=comment,
                headless=headless
            )
            print("\n[SUCCESS] Browser automation completed successfully!")
            print(f"          Report Created: {result.get('report_name')}")
            print(f"          Screenshots folder: {result.get('screenshot_folder')}")
            print(f"          Notes:          {result.get('notes')}")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Browser automation failed:")
            print(f"        {str(e)}")
            print("        Screenshots on failure are saved in the 'screenshots' folder.")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow E: Browser Delete Report
    # ----------------------------------------------------
    elif args.command == "delete-report":
        report_name_val = args.report_name
        print("=" * 60)
        print(f"     SAP Concur Browser-Based Delete Report: '{report_name_val}'")
        print("=" * 60)
        
        try:
            browser_client = ConcurBrowserClient()
            browser_client.delete_report(name=report_name_val, headless=True)
            print(f"\n[SUCCESS] Successfully deleted report: '{report_name_val}'")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to delete report: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow F: Delete All Reports
    # ----------------------------------------------------
    elif args.command == "delete-all-reports":
        print("=" * 60)
        print("   SAP Concur Browser-Based Delete All Reports")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            print("[*] Querying reports...")
            reports = browser_client.list_reports(headless=True)
            print(f"[*] Discovered {len(reports)} report(s).")
            for r in reports:
                name = r.get("name")
                print(f"[*] Deleting report: '{name}'...")
                browser_client.delete_report(name=name, headless=True)
            print("\n[SUCCESS] All reports deleted.")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to delete all reports: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow G: Delete All Receipts
    # ----------------------------------------------------
    elif args.command == "delete-all-receipts":
        print("=" * 60)
        print("   SAP Concur Browser-Based Delete All Receipts")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            print("[*] Querying available receipts...")
            receipts = browser_client.list_available_receipts(headless=True)
            print(f"[*] Discovered {len(receipts)} receipt(s).")
            for r_name in receipts:
                print(f"[*] Deleting receipt: '{r_name}'...")
                browser_client.delete_available_receipt(receipt_name=r_name, headless=True)
            print("\n[SUCCESS] All available receipts deleted.")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to delete all receipts: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow H: Delete All Reports AND Receipts (Nuke)
    # ----------------------------------------------------
    elif args.command == "nuke":
        print("=" * 60)
        print("   SAP Concur Browser-Based Nuke (Delete All Reports & Receipts)")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            
            # Reports
            print("[*] Querying reports...")
            reports = browser_client.list_reports(headless=True)
            print(f"[*] Discovered {len(reports)} report(s).")
            for r in reports:
                name = r.get("name")
                print(f"[*] Deleting report: '{name}'...")
                browser_client.delete_report(name=name, headless=True)
                
            # Receipts
            print("\n[*] Querying available receipts...")
            receipts = browser_client.list_available_receipts(headless=True)
            print(f"[*] Discovered {len(receipts)} receipt(s).")
            for r_name in receipts:
                print(f"[*] Deleting receipt: '{r_name}'...")
                browser_client.delete_available_receipt(receipt_name=r_name, headless=True)
                
            print("\n[SUCCESS] All reports and receipts deleted.")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to delete all items: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow I: Query Historical (Old) Reports
    # ----------------------------------------------------
    elif args.command == "list-old-reports":
        filter_val = args.filter_view
        print("=" * 60)
        print(f"     SAP Concur Browser-Based Historical Reports (Filter: {filter_val})")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            reports = browser_client.list_reports(filter_view=filter_val, headless=True)
            print(f"[SUCCESS] Discovered {len(reports)} historical report(s):")
            for idx, r in enumerate(reports, 1):
                print(f"  {idx}. {r.get('name')} (Purpose: {r.get('purpose', 'None')})")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Historical reports query failed: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow J: Report Details of a Report
    # ----------------------------------------------------
    elif args.command == "report-details":
        report_name_val = args.report_name
        filter_val = args.filter_view
        print("=" * 60)
        print(f"     SAP Concur Report Details: '{report_name_val}'")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            details = browser_client.get_report_details(name=report_name_val, filter_view=filter_val, headless=True)
            print(f"[SUCCESS] Details retrieved:")
            print(f"  Name:     {details.get('report_name')}")
            print(f"  Number:   {details.get('report_number')}")
            print(f"  Purpose:  {details.get('purpose')}")
            print(f"  Comment:  {details.get('comment')}")
            print(f"  Expenses: ({len(details.get('expenses'))} items)")
            for item in details.get('expenses'):
                print(f"    - {item.get('raw_text')}")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to get report details: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow K: List Card Transactions
    # ----------------------------------------------------
    elif args.command == "list-cards":
        filter_val = args.filter_view
        print("=" * 60)
        print(f"     SAP Concur Card Transactions (Filter: {filter_val})")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            txs = browser_client.list_card_transactions(card_type_filter=filter_val, headless=True)
            print(f"[SUCCESS] Discovered {len(txs)} transaction(s):")
            for idx, t in enumerate(txs, 1):
                print(f"  {idx}. {t.get('raw_text')}")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Listing card transactions failed: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow L: Get Card Transaction Details
    # ----------------------------------------------------
    elif args.command == "card-details":
        tx_id = args.merchant_or_id
        filter_val = args.filter_view
        print("=" * 60)
        print(f"     SAP Concur Card Transaction Details: '{tx_id}'")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            details = browser_client.get_card_transaction_details(merchant_or_id=tx_id, card_type_filter=filter_val, headless=True)
            print(f"[SUCCESS] Transaction details:")
            print(f"  Merchant:     {details.get('merchant')}")
            print(f"  Date:         {details.get('date')}")
            print(f"  Amount:       {details.get('amount')}")
            print(f"  ID:           {details.get('transaction_id')}")
            print(f"  Card Program: {details.get('card_program')}")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to get transaction details: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow M: Add Delegate
    # ----------------------------------------------------
    elif args.command == "add-delegate":
        name = args.name_or_email
        perms = args.delegate_perms
        print("=" * 60)
        print(f"     SAP Concur Add Expense Delegate: '{name}'")
        print(f"     Permissions: {perms}")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            browser_client.add_expense_delegate(name_or_email=name, permissions=perms, headless=True)
            print(f"\n[SUCCESS] Delegate '{name}' added successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to add delegate: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow N: Remove Delegate
    # ----------------------------------------------------
    elif args.command == "remove-delegate":
        name = args.name_or_email
        print("=" * 60)
        print(f"     SAP Concur Remove Expense Delegate: '{name}'")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            browser_client.remove_expense_delegate(name_or_email=name, headless=True)
            print(f"\n[SUCCESS] Delegate '{name}' removed successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to remove delegate: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow O: Reconcile Report Transactions
    # ----------------------------------------------------
    elif args.command == "reconcile":
        report_name_val = args.report_name
        rules_path = args.reconcile_rules
        import json
        
        reconciliation_rules = {
            "Uber": {
                "expense_type": "Ground Transportation",
                "business_purpose": "Client dinner ride",
                "comment": "Uber Ride",
                "allocation_code": "COST-01"
            },
            "Office Depot": {
                "expense_type": "Office Supplies",
                "business_purpose": "Team materials",
                "comment": "Pens and notebooks",
                "allocation_code": "COST-02"
            }
        }
        
        if rules_path:
            try:
                with open(rules_path, "r") as f:
                    reconciliation_rules = json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load reconciliation rules JSON from '{rules_path}': {str(e)}")
                sys.exit(1)
                
        print("=" * 60)
        print(f"     SAP Concur Report Reconciliation: '{report_name_val}'")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            res = browser_client.reconcile_report(
                report_name=report_name_val,
                reconciliation_rules=reconciliation_rules,
                headless=True,
                submit=args.submit
            )
            if args.submit:
                print(f"\n[SUCCESS] Report '{report_name_val}' reconciled and submitted successfully!")
            else:
                print(f"\n[SUCCESS] Report '{report_name_val}' reconciled successfully! (Draft mode, not submitted)")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Reconciliation failed: {str(e)}")
            print("=" * 60)
            sys.exit(1)

    # ----------------------------------------------------
    # Flow P: Attach Receipt to Transaction
    # ----------------------------------------------------
    elif args.command == "attach-receipt":
        report_name_val = args.report_name
        merchant = args.merchant
        receipt_path = args.receipt_path

        print("=" * 60)
        print(f"     SAP Concur Attach Receipt: '{receipt_path}' to '{merchant}' in '{report_name_val}'")
        print("=" * 60)
        try:
            browser_client = ConcurBrowserClient()
            browser_client.attach_receipt_to_transaction(
                report_name=report_name_val,
                merchant_or_id=merchant,
                receipt_file_path=receipt_path,
                headless=True
            )
            print(f"\n[SUCCESS] Receipt '{receipt_path}' attached successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Failed to attach receipt: {str(e)}")
            print("=" * 60)
            sys.exit(1)


if __name__ == "__main__":
    run_tests()
