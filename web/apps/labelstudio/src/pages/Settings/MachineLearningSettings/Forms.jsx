import { useState } from "react";
import { Button } from "@humansignal/ui";
import { ErrorWrapper } from "../../../components/Error/Error";
import { InlineError } from "../../../components/Error/InlineError";
import { Form, Input, Select, TextArea, Toggle } from "../../../components/Form";
import "./MachineLearningSettings.scss";
import { t } from "@humansignal/i18n";

const CustomBackendForm = ({ action, backend, project, onSubmit }) => {
  const [selectedAuthMethod, setAuthMethod] = useState("NONE");
  const [, setMLError] = useState();

  return (
    <Form
      action={action}
      formData={{ ...(backend ?? {}) }}
      params={{ pk: backend?.id }}
      onSubmit={async (response) => {
        if (!response.error_message) {
          onSubmit(response);
        }
      }}
    >
      <Input type="hidden" name="project" value={project.id} />

      <Form.Row columnCount={1}>
        <Input name="title" label={t("pages.settings.machine_learning_settings.forms.name")} placeholder={t("pages.settings.machine_learning_settings.forms.enter_a_name")} required />
      </Form.Row>

      <Form.Row columnCount={1}>
        <Input name="url" label={t("pages.settings.machine_learning_settings.forms.backend_url")} required />
      </Form.Row>

      <Form.Row columnCount={2}>
        <Select
          name="auth_method"
          label={t("pages.settings.machine_learning_settings.forms.select_authentication_method")}
          options={[
            { label: "No Authentication", value: "NONE" },
            { label: "Basic Authentication", value: "BASIC_AUTH" },
          ]}
          value={selectedAuthMethod}
          onChange={setAuthMethod}
        />
      </Form.Row>

      {(backend?.auth_method === "BASIC_AUTH" || selectedAuthMethod === "BASIC_AUTH") && (
        <Form.Row columnCount={2}>
          <Input name="basic_auth_user" label={t("pages.settings.machine_learning_settings.forms.basic_auth_user")} />
          {backend?.basic_auth_pass_is_set ? (
            <Input name="basic_auth_pass" label={t("pages.settings.machine_learning_settings.forms.basic_auth_pass")} type="password" placeholder="********" />
          ) : (
            <Input name="basic_auth_pass" label={t("pages.settings.machine_learning_settings.forms.basic_auth_pass")} type="password" />
          )}
        </Form.Row>
      )}

      <Form.Row columnCount={1}>
        <TextArea
          name="extra_params"
          label={t("pages.settings.machine_learning_settings.forms.any_extra_params_to_pass")}
          style={{ minHeight: 120 }}
        />
      </Form.Row>

      <Form.Row columnCount={1}>
        <Toggle
          name="is_interactive"
          label={t("pages.settings.machine_learning_settings.forms.interactive_preannotations")}
          description={t("pages.settings.machine_learning_settings.forms.if_enabled_some_labeling_tools")}
        />
      </Form.Row>

      <Form.Actions>
        <Button type="submit" look="primary" onClick={() => setMLError(null)} aria-label={t("pages.settings.machine_learning_settings.forms.save_machine_learning_form")}>
          {t("pages.settings.machine_learning_settings.forms.validate_and_save")}
        </Button>
      </Form.Actions>

      <Form.ResponseParser>
        {(response) => (
          <>
            {response.error_message && (
              <ErrorWrapper
                error={{
                  response: {
                    detail: `Failed to ${backend ? "save" : "add new"} ML backend.`,
                    exc_info: response.error_message,
                  },
                }}
              />
            )}
          </>
        )}
      </Form.ResponseParser>

      <InlineError />
    </Form>
  );
};

export { CustomBackendForm };
