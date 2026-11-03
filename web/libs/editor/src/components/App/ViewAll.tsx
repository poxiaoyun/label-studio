import { usePersistentState } from "@humansignal/core/lib/hooks/usePersistentState";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@humansignal/ui/lib/tabs";
import type { MSTAnnotation, MSTStore } from "../../stores/types";
import TaskSummary from "../TaskSummary/TaskSummary";
import Grid from "./Grid";
import { t } from "@humansignal/i18n";

type Props = {
  store: MSTStore["annotationStore"];
  annotations: MSTAnnotation[];
  root: any;
};

export const ViewAll = ({ store: annotationStore, annotations, root }: Props) => {
  const [tab, setTab] = usePersistentState<"summary" | "compare">("view-all-tab", "summary");

  if (annotationStore.store.hasInterface("annotations:summary")) {
    return (
      <div className="px-base pt-tighter mt-base">
        <Tabs variant="default" value={tab} onValueChange={(value) => setTab(value as "summary" | "compare")}>
          <TabsList>
            <TabsTrigger value="summary" data-testid="compare-all-summary-tab">
              {t("lsf.components.app.view_all.summary")}
            </TabsTrigger>
            <TabsTrigger value="compare" data-testid="compare-all-side-by-side-tab">
              {t("lsf.components.app.view_all.side_by_side")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="summary">
            <TaskSummary store={annotationStore} annotations={annotations} />
          </TabsContent>

          <TabsContent value="compare">
            <Grid store={annotationStore} annotations={annotations} root={root} />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  return <Grid store={annotationStore} annotations={annotations} root={root} />;
};
