import { inject, observer } from "mobx-react";
import { RadioGroup } from "../../Common/RadioGroup/RadioGroup";
import { IconGrid, IconList } from "@humansignal/icons";
import { Tooltip } from "@humansignal/ui";
import { t } from "@humansignal/i18n";

const viewInjector = inject(({ store }) => ({
  view: store.currentView,
}));

export const ViewToggle = viewInjector(
  observer(({ view, size, ...rest }) => {
    return (
      <RadioGroup
        size={size}
        value={view.type}
        onChange={(e) => view.setType(e.target.value)}
        {...rest}
        style={{ "--button-padding": "0 var(--spacing-tighter)" }}
      >
        <Tooltip title={t("dm.data_manager.toolbar.view_toggle.list_view")}>
          <div>
            <RadioGroup.Button value="list" aria-label={t("dm.data_manager.toolbar.view_toggle.switch_to_list_view")}>
              <IconList />
            </RadioGroup.Button>
          </div>
        </Tooltip>
        <Tooltip title={t("dm.data_manager.toolbar.view_toggle.grid_view")}>
          <div>
            <RadioGroup.Button value="grid" aria-label={t("dm.data_manager.toolbar.view_toggle.switch_to_grid_view")}>
              <IconGrid />
            </RadioGroup.Button>
          </div>
        </Tooltip>
      </RadioGroup>
    );
  }),
);

export const DataStoreToggle = viewInjector(({ view, size, ...rest }) => {
  return (
    <RadioGroup value={view.target} size={size} onChange={(e) => view.setTarget(e.target.value)} {...rest}>
      <RadioGroup.Button value="tasks">{t("dm.data_manager.toolbar.view_toggle.tasks")}</RadioGroup.Button>
      <RadioGroup.Button value="annotations" disabled>
        {t("dm.data_manager.toolbar.view_toggle.annotations")}
      </RadioGroup.Button>
    </RadioGroup>
  );
});
