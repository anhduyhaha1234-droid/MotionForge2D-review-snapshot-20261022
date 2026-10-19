param(
    [ValidateSet("READY", "BLOCKED", "DECISION", "TEST")]
    [string]$Type = "TEST",
    [string]$Task = "",
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$shell = New-Object -ComObject WScript.Shell

switch ($Type) {
    "READY" {
        $title = "MotionForge2D - Ready for final review"
        $body = "Hermes completed the roadmap and final quality checks.`n`nOpen Codex and send:`nReview tong the MotionForge2D va ban giao ban su dung duoc."
        $icon = 64
    }
    "BLOCKED" {
        $title = "MotionForge2D - Autopilot needs Codex"
        $body = "Hermes is blocked at $Task.`n`n$Message`n`nOpen Codex and send:`nKiem tra blocker Autopilot va tiep tuc."
        $icon = 48
    }
    "DECISION" {
        $title = "MotionForge2D - Decision needed"
        $body = "Hermes needs a decision at $Task.`n`n$Message`n`nOpen MF-Autopilot-Main or ask Codex."
        $icon = 32
    }
    default {
        $title = "MotionForge2D - Popup test"
        $body = "The Autopilot popup works.`n`nWhen a BLOCKED or READY popup appears, open Codex and send the exact displayed sentence."
        $icon = 64
    }
}

# 0 seconds means the popup remains until the user acknowledges it.
[void]$shell.Popup($body, 0, $title, $icon)
