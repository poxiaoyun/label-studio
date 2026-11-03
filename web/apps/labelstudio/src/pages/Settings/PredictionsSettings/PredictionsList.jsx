import { useCallback, useContext } from "react";

import { format, formatDistanceToNow, parseISO } from "date-fns";
import { Menu } from "../../../components";
import { Button, Dropdown } from "@humansignal/ui";
import { IconInfoOutline, IconPredictions, IconEllipsis } from "@humansignal/icons";
import { Tooltip } from "@humansignal/ui";
import { confirm } from "../../../components/Modal/Modal";
import { ApiContext } from "../../../providers/ApiProvider";
import { cn } from "../../../utils/bem";

import "./PredictionsList.scss";
import { t } from "@humansignal/i18n";

export const PredictionsList = ({ project, versions, fetchVersions }) => {
  const api = useContext(ApiContext);

  const onDelete = useCallback(
    async (version) => {
      await api.callApi("deletePredictions", {
        params: {
          pk: project.id,
        },
        body: {
          model_version: version.model_version,
        },
      });
      await fetchVersions();
    },
    [fetchVersions, api],
  );

  return (
    <div style={{ maxWidth: 680 }}>
      {versions.map((v) => (
        <VersionCard key={v.model_version} version={v} onDelete={onDelete} />
      ))}
    </div>
  );
};

const VersionCard = ({ version, selected, onSelect, editable, onDelete }) => {
  const rootClass = cn("prediction-card");

  const confirmDelete = useCallback(
    (version) => {
      confirm({
        title: t("settings.predictions.delete"),
        body: "This action cannot be undone. Are you sure?",
        buttonLook: "destructive",
        onOk() {
          onDelete?.(version);
        },
      });
    },
    [version, onDelete],
  );

  return (
    <div className={rootClass.toClassName()}>
      <div>
        <div className={rootClass.elem("title").toClassName()}>
          {version.model_version}
          {version.model_version === "undefined" && (
            <Tooltip title={t("pages.settings.predictions_settings.predictions_list.model_version_is_undefined_likely")}>
              <IconInfoOutline className={cn("help-icon").toClassName()} width="14" height="14" />
            </Tooltip>
          )}
        </div>
        <div className={rootClass.elem("meta").toClassName()}>
          <div className={rootClass.elem("group").toClassName()}>
            <IconPredictions />
            &nbsp;{version.count}
          </div>
          <div className={rootClass.elem("group").toClassName()}>
            {t("settings.predictions.last_created")}&nbsp;
            <Tooltip title={format(parseISO(version.latest), "yyyy-MM-dd HH:mm:ss")}>
              <span>
                {formatDistanceToNow(parseISO(version.latest), {
                  addSuffix: true,
                })}
              </span>
            </Tooltip>
          </div>
        </div>
      </div>
      <div className={rootClass.elem("menu").toClassName()}>
        <Dropdown.Trigger
          align="right"
          content={
            <Menu size="medium" contextual>
              <Menu.Item onClick={() => confirmDelete(version)} isDangerous>
                {t("pages.settings.predictions_settings.predictions_list.delete")}
              </Menu.Item>
            </Menu>
          }
        >
          <Button look="string">
            <IconEllipsis />
          </Button>
        </Dropdown.Trigger>
      </div>
    </div>
  );
};
