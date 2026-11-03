import { useCallback, useState } from "react";
import { Button } from "@humansignal/ui";
import { useAPI } from "../../../providers/ApiProvider";
import { Typography } from "@humansignal/ui";
import { t } from "@humansignal/i18n";

export const StartModelTraining = ({ backend }) => {
  const api = useAPI();
  const [response, setResponse] = useState(null);

  const onStartTraining = useCallback(
    async (backend) => {
      const res = await api.callApi("trainMLBackend", {
        params: {
          pk: backend.id,
        },
      });

      setResponse(res.response || {});
    },
    [api],
  );

  return (
    <div className="max-w-[680px]">
      <Typography size="small" className="text-neutral-content-subtler">
        {t("pages.settings.machine_learning_settings.start_model_training.youre_about_to_manually_trigger")}
      </Typography>
      <Typography size="small" className="text-neutral-content-subtler mt-base mb-wide">
        *Note: Currently, there is no built-in feedback loop within this interface for tracking the training progress.
        You'll need to monitor the model's training steps directly through the model's own tools and environment.
      </Typography>

      {!response && (
        <Button
          onClick={() => {
            onStartTraining(backend);
          }}
        >
          {t("pages.settings.machine_learning_settings.start_model_training.start_training")}
        </Button>
      )}

      {!!response && (
        <>
          <pre>Request Sent!</pre>
          <pre>Response: {JSON.stringify(response, null, 2)}</pre>
        </>
      )}
    </div>
  );
};
