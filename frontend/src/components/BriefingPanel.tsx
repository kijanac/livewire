import { BriefingShell } from "./briefing/BriefingShell";

interface BriefingPanelProps {
  billId: number;
  onClose: () => void;
  onNavigate?: (billId: number) => void;
}

function BriefingPanel(props: BriefingPanelProps) {
  return <BriefingShell {...props} />;
}

export default BriefingPanel;
