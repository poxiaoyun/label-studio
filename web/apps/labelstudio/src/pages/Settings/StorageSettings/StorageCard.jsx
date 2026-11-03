import { useCallback, useContext, useEffect, useState } from "react";
import { Card, Menu } from "../../../components";
import { Button, Dropdown } from "@humansignal/ui";
import { ApiContext } from "../../../providers/ApiProvider";
import { StorageSummary } from "./StorageSummary";
import { IconEllipsisVertical } from "@humansignal/icons";
import { t } from "@humansignal/i18n";

export const StorageCard = ({ rootClass, target, storage, onEditStorage, onDeleteStorage, storageTypes }) => {
  const [syncing, setSyncing] = useState(false);
  const api = useContext(ApiContext);
  const [storageData, setStorageData] = useState({ ...storage });
  const [synced, setSynced] = useState(null);

  const startSync = useCallback(async () => {
    setSyncing(true);
    setSynced(null);

    const result = await api.callApi("syncStorage", {
      params: {
        target,
        type: storageData.type,
        pk: storageData.id,
      },
    });

    if (result) {
      setStorageData(result);
      setSynced(result.last_sync_count);
    }

    setSyncing(false);
  }, [storage]);

  useEffect(() => {
    setStorageData(storage);
  }, [storage]);

  const notSyncedYet = synced !== null || ["in_progress", "queued"].includes(storageData.status);

  return (
    <Card
      header={storageData.title ?? `Untitled ${storageData.type}`}
      extra={
        <Dropdown.Trigger
          align="right"
          content={
            <Menu size="compact" style={{ width: 110 }}>
              <Menu.Item onClick={() => onEditStorage(storageData)}>{t("pages.settings.storage_settings.storage_card.edit")}</Menu.Item>
              <Menu.Item onClick={() => onDeleteStorage(storageData)}>{t("pages.settings.storage_settings.storage_card.delete")}</Menu.Item>
            </Menu>
          }
        >
          <Button look="string" className="-ml-3" aria-label={t("pages.settings.storage_settings.storage_card.storage_options")}>
            <IconEllipsisVertical />
          </Button>
        </Dropdown.Trigger>
      }
    >
      <StorageSummary
        target={target}
        storage={storageData}
        className={rootClass.elem("summary").toClassName()}
        storageTypes={storageTypes}
      />
      <div className={rootClass.elem("sync").toClassName()}>
        <div className="mt-base">
          <Button
            look="outlined"
            waiting={syncing}
            onClick={startSync}
            disabled={notSyncedYet}
            aria-label={t("pages.settings.storage_settings.storage_card.sync_storage")}
          >
            {t("pages.settings.storage_settings.storage_card.sync_storage")}
          </Button>
          {notSyncedYet && (
            <div className={rootClass.elem("sync-count").toClassName()}>
              {t("pages.settings.storage_settings.storage_card.syncing_may_take_some_time")}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
