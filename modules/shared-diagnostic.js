import { execSync } from "child_process";

export function runPowerShellDiagnostic(command) {
  try {
    // Show exactly what's being sent
    const trimmedCommand = command.trim();
    const fullCommand = `powershell -NoProfile -Command "${trimmedCommand}"`;

    console.error("\n=== DIAGNOSTIC: Command Execution ===");
    console.error("ORIGINAL (raw):", JSON.stringify(command.substring(0, 100)));
    console.error("");
    console.error("AFTER trim():", JSON.stringify(trimmedCommand.substring(0, 100)));
    console.error("");
    console.error("FULL COMMAND BEING EXECUTED:");
    console.error(fullCommand);
    console.error("");
    console.error("COMMAND LENGTH:", fullCommand.length);
    console.error("Contains newlines:", fullCommand.includes('\n') ? 'YES' : 'NO');
    console.error("Contains pipes:", fullCommand.includes('|') ? 'YES' : 'NO');
    console.error("");

    // Execute and show result
    const output = execSync(fullCommand, { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });

    console.error("RESULT: ✅ SUCCESS");
    console.error("OUTPUT LENGTH:", output.length);
    console.error("=== END DIAGNOSTIC ===\n");

    return { success: true, data: output };
  } catch (error) {
    console.error("\n=== DIAGNOSTIC: Command Failed ===");
    console.error("ERROR TYPE:", error.constructor.name);
    console.error("ERROR MESSAGE:", error.message.substring(0, 500));
    console.error("=== END DIAGNOSTIC ===\n");

    return { success: false, error: error.message };
  }
}

// Test with firewall command that fails
const testCommand = `
  Get-NetFirewallProfile |
  Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
  ConvertTo-Json
`;

console.log("Testing firewall command diagnostic...");
const result = runPowerShellDiagnostic(testCommand);
console.log("Final result success:", result.success);
