import { settingsAtom, TOKEN_SETTINGS_KEY } from "@humansignal/app-common/pages/AccountSettings/atoms";
import type { AuthTokenSettings } from "@humansignal/app-common/pages/AccountSettings/types";
import { Button } from "@humansignal/ui";
import { Form, Input, Toggle } from "apps/labelstudio/src/components/Form";
import { useAtomValue } from "jotai";
import { queryClientAtom } from "jotai-tanstack-query";
import { type ChangeEvent, useState } from "react";
import { t } from "@humansignal/i18n";

export const TokenSettingsModal = ({ showTTL, onSaved }: { showTTL?: boolean; onSaved?: () => void }) => {
  const settings = useAtomValue(settingsAtom);
  if (!settings.isSuccess || settings.isError || "error" in settings.data) {
    return <div>{t("appcommon.blocks.token_settings_modal.index.error_loading_settings")}</div>;
  }
  return (
    <TokenSettingsModalView
      key={settings.data?.api_tokens_enabled}
      settings={settings.data}
      showTTL={showTTL}
      onSaved={onSaved}
    />
  );
};

function TokenSettingsModalView({
  settings,
  showTTL,
  onSaved,
}: {
  settings: AuthTokenSettings;
  showTTL?: boolean;
  onSaved?: () => void;
}) {
  const [enableTTL, setEnableTTL] = useState(settings.api_tokens_enabled);
  const queryClient = useAtomValue(queryClientAtom);
  const reloadSettings = () => {
    queryClient.invalidateQueries({ queryKey: [TOKEN_SETTINGS_KEY] });
    onSaved?.();
  };
  return (
    <Form action="accessTokenUpdateSettings" onSubmit={reloadSettings}>
      <Form.Row columnCount={1}>
        <Toggle
          label={t("appcommon.blocks.token_settings_modal.index.personal_access_tokens")}
          name="api_tokens_enabled"
          description={t("appcommon.blocks.token_settings_modal.index.enable_increased_token_authentication_security")}
          checked={settings.api_tokens_enabled ?? true}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setEnableTTL(e.target.checked)}
        />
      </Form.Row>
      <Form.Row columnCount={1}>
        <Toggle
          label={t("appcommon.blocks.token_settings_modal.index.legacy_tokens")}
          name="legacy_api_tokens_enabled"
          description={t("appcommon.blocks.token_settings_modal.index.enable_legacy_access_tokens_these")}
          checked={settings.legacy_api_tokens_enabled ?? false}
        />
      </Form.Row>
      {showTTL === true && (
        <Form.Row columnCount={1}>
          <Input
            name="api_token_ttl_days"
            label={t("appcommon.blocks.token_settings_modal.index.time_to_live_optional_personal_access_token")}
            description={t("appcommon.blocks.token_settings_modal.index.the_number_of_days_after")}
            labelProps={{
              description:
                "The number of days, after creation, that the token will be valid for. After this time period a user will need to create a new access token",
            }}
            disabled={!enableTTL}
            type="number"
            min={10}
            max={365}
            value={settings.api_token_ttl_days ?? 30}
          />
        </Form.Row>
      )}
      <Form.Actions>
        <Button variant="primary" look="filled" type="submit">
          {t("appcommon.blocks.token_settings_modal.index.save_changes")}
        </Button>
      </Form.Actions>
    </Form>
  );
}
