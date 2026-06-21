import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "@sinclair/typebox";
import { exec } from "child_process";
import { promisify } from "util";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

const execAsync = promisify(exec);

export default function (pi: ExtensionAPI) {
  // Helper to find the absolute path of run.sh in the project workspace
  const getLauncherPath = (): string => {
    // Attempt to use current directory or locate run.sh in parent directories
    let dir = process.cwd();
    while (dir && dir !== path.parse(dir).root) {
      const launcher = path.join(dir, "run.sh");
      if (fs.existsSync(launcher)) {
        return launcher;
      }
      dir = path.dirname(dir);
    }
    return "./run.sh"; // Fallback to relative
  };

  const runCommand = async (args: string[]): Promise<string> => {
    const launcher = getLauncherPath();
    const cmd = `"${launcher}" ${args.map(a => `"${a.replace(/"/g, '\\"')}"`).join(" ")}`;
    
    try {
      const { stdout, stderr } = await execAsync(cmd, { cwd: path.dirname(launcher) });
      return stdout + "\n" + stderr;
    } catch (error: any) {
      throw new Error(`Execution failed: ${error.message}\nOutput: ${error.stdout || ""}\nError: ${error.stderr || ""}`);
    }
  };

  // 1. Tool: concur_list_reports
  pi.registerTool({
    name: "concur_list_reports",
    label: "List Concur Reports",
    description: "Queries and lists active or historical expense reports in SAP Concur.",
    parameters: Type.Object({
      filter_view: Type.Optional(Type.String({
        description: "Dropdown filter to apply (e.g., 'Last 90 Days', 'All Reports', 'Active Reports')",
        default: "Last 90 Days"
      })),
      is_old: Type.Optional(Type.Boolean({
        description: "Set true to query historical reports, false for current active/draft reports",
        default: true
      }))
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const filter = params.filter_view || "Last 90 Days";
      const isOld = params.is_old !== false;
      
      const args = isOld ? ["browser-query-old", filter] : ["browser-query"];
      const output = await runCommand(args);
      
      return {
        content: [{ type: "text", text: output }],
        details: {}
      };
    }
  });

  // 2. Tool: concur_report_details
  pi.registerTool({
    name: "concur_report_details",
    label: "Get Concur Report Details",
    description: "Fetches full metadata and line-item details of a specific expense report by name.",
    parameters: Type.Object({
      report_name: Type.String({ description: "The exact name of the target expense report" }),
      filter_view: Type.Optional(Type.String({
        description: "The view filter to look inside (e.g., 'Last 90 Days', 'All Reports')",
        default: "Last 90 Days"
      }))
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const filter = params.filter_view || "Last 90 Days";
      const output = await runCommand(["browser-report-details", params.report_name, filter]);
      
      return {
        content: [{ type: "text", text: output }],
        details: {}
      };
    }
  });

  // 3. Tool: concur_list_cards
  pi.registerTool({
    name: "concur_list_card_transactions",
    label: "List Card Transactions",
    description: "Queries and lists credit card transactions inside the Available Expenses section.",
    parameters: Type.Object({
      filter_view: Type.Optional(Type.String({
        description: "The activity filter to apply (e.g., 'All Corporate and Personal Cards', 'All Purchasing Cards')",
        default: "All Corporate and Personal Cards"
      }))
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const filter = params.filter_view || "All Corporate and Personal Cards";
      const output = await runCommand(["browser-list-cards", filter]);
      
      return {
        content: [{ type: "text", text: output }],
        details: {}
      };
    }
  });

  // 4. Tool: concur_reconcile_report
  pi.registerTool({
    name: "concur_reconcile_report",
    label: "Reconcile Concur Report",
    description: "Automates month-end reconciliation: fills in Expense Type, Purpose, Comment, and Allocation Codes for each transaction in the report, and submits the report.",
    parameters: Type.Object({
      report_name: Type.String({ description: "Name of the draft expense report to reconcile" }),
      rules: Type.String({
        description: "JSON string representing mapping rules. Keys are merchant names (e.g., 'Uber'), values map to expense_type, business_purpose, comment, allocation_code."
      })
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      // Validate JSON rules
      let rulesObj;
      try {
        rulesObj = JSON.parse(params.rules);
      } catch (err: any) {
        throw new Error(`Invalid JSON rules input: ${err.message}`);
      }

      // Write rules temporarily to file
      const tempFile = path.join(os.tmpdir(), `concur-recon-${Date.now()}.json`);
      fs.writeFileSync(tempFile, JSON.stringify(rulesObj, null, 2));

      try {
        const output = await runCommand(["browser-reconcile", params.report_name, tempFile]);
        return {
          content: [{ type: "text", text: output }],
          details: {}
        };
      } finally {
        if (fs.existsSync(tempFile)) {
          fs.unlinkSync(tempFile);
        }
      }
    }
  });

  // 5. Tool: concur_attach_receipt
  pi.registerTool({
    name: "concur_attach_receipt",
    label: "Attach Receipt to Expense",
    description: "Attaches a local receipt image or PDF file directly to a transaction inside an expense report.",
    parameters: Type.Object({
      report_name: Type.String({ description: "Name of the expense report containing the transaction" }),
      merchant: Type.String({ description: "Merchant name or transaction ID to match receipt against (e.g., 'Uber')" }),
      receipt_path: Type.String({ description: "Absolute local path to the receipt file (PDF or image)" })
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const output = await runCommand([
        "browser-attach-receipt",
        params.report_name,
        params.merchant,
        params.receipt_path
      ]);
      
      return {
        content: [{ type: "text", text: output }],
        details: {}
      };
    }
  });
}
