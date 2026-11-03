import { Tabs, TabsList, TabsTrigger } from "@humansignal/ui";
import { t } from "@humansignal/i18n";

export type ViewMode = "code" | "interactive";

interface ViewToggleProps {
  /** Current view mode (code or interactive) */
  view: ViewMode;
  /** Callback when view mode changes */
  onViewChange: (view: ViewMode) => void;
  /** Additional CSS class */
  className?: string;
}

/**
 * ViewToggle - Controls for switching between Code and Interactive view modes
 */
export const ViewToggle = ({ view, onViewChange, className }: ViewToggleProps) => {
  return (
    <Tabs value={view} onValueChange={(newValue: string) => onViewChange(newValue as ViewMode)} variant="default">
      <TabsList className={className}>
        <TabsTrigger value="code">{t("dm.common.task_source_viewer.view_toggle.code")}</TabsTrigger>
        <TabsTrigger value="interactive">{t("dm.common.task_source_viewer.view_toggle.interactive")}</TabsTrigger>
      </TabsList>
    </Tabs>
  );
};
