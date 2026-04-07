const JOURNEY_STATE_KEYS = {
  complete: "common.journeyStates.complete",
  active: "common.journeyStates.active",
  attention: "common.journeyStates.attention",
  todo: "common.journeyStates.todo",
} as const;

const WORKFLOW_STATE_KEYS = {
  new: "common.workflowStates.new",
  pending: "common.workflowStates.pending",
  queued: "common.workflowStates.queued",
  running: "common.workflowStates.running",
  completed: "common.workflowStates.completed",
  failed: "common.workflowStates.failed",
  verified: "common.workflowStates.verified",
} as const;

export type JourneyStateLabel = keyof typeof JOURNEY_STATE_KEYS;

export function getJourneyStateLabel(
  translate: (key: string, values?: Record<string, unknown>) => string,
  state: JourneyStateLabel,
) {
  return translate(JOURNEY_STATE_KEYS[state]);
}

export function getWorkflowStateLabel(
  translate: (key: string, values?: Record<string, unknown>) => string,
  status?: string | null,
) {
  if (!status) {
    return "";
  }

  const key = WORKFLOW_STATE_KEYS[status as keyof typeof WORKFLOW_STATE_KEYS];
  return key ? translate(key) : status;
}
