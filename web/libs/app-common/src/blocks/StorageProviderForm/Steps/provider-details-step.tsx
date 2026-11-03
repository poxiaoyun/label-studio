import { getProviderConfig } from "../providers";
import { ProviderForm } from "../components/provider-form";
import Input from "apps/labelstudio/src/components/Form/Elements/Input/Input";
import { Toggle } from "@humansignal/ui";
import { t } from "@humansignal/i18n";

interface ProviderDetailsStepProps {
  formData: any;
  errors: Record<string, string>;
  handleProviderFieldChange: (name: string, value: any) => void;
  handleFieldBlur?: (name: string, value: any) => void;
  provider?: string;
  isEditMode?: boolean;
  target?: "import" | "export";
}

export const ProviderDetailsStep = ({
  formData,
  errors,
  handleProviderFieldChange,
  handleFieldBlur,
  provider,
  isEditMode = false,
  target,
}: ProviderDetailsStepProps) => {
  const providerConfig = getProviderConfig(provider);

  if (!provider || !providerConfig) {
    return <div className="text-red-500">{!provider ? "No provider selected" : `Unknown provider: ${provider}`}</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">{providerConfig.title}</h2>
        <p className="text-muted-foreground">{providerConfig.description}</p>
      </div>

      {/* Title field - common for all providers */}
      <div className="space-y-2">
        <Input
          name="title"
          value={formData.title ?? ""}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleProviderFieldChange("title", e.target.value)}
          placeholder={t("appcommon.storage_provider_form.steps.provider_details_step.enter_a_descriptive_name_e_g")}
          validate=""
          skip={false}
          labelProps={{}}
          ghost={false}
          tooltip=""
          tooltipIcon={null}
          required={true}
          label={t("appcommon.storage_provider_form.steps.provider_details_step.storage_title")}
          description={t("appcommon.storage_provider_form.steps.provider_details_step.this_name_will_help_you")}
          footer={errors.title ? <span className="text-negative-content">{errors.title}</span> : ""}
          className={errors.title ? "border-negative-content" : ""}
        />
      </div>

      <ProviderForm
        provider={providerConfig}
        formData={formData}
        errors={errors}
        onChange={handleProviderFieldChange}
        onBlur={handleFieldBlur}
        isEditMode={isEditMode}
        target={target}
      />

      {/* Export-specific common fields */}
      {target === "export" && (
        <div className="space-y-6">
          <div className="space-y-2">
            <Toggle
              checked={formData.can_delete_objects ?? false}
              onChange={(e) => handleProviderFieldChange("can_delete_objects", e.target.checked)}
              aria-label={t("appcommon.storage_provider_form.steps.provider_details_step.can_delete_objects_from_storage")}
              label={t("appcommon.storage_provider_form.steps.provider_details_step.can_delete_objects_from_storage")}
              description={t("appcommon.storage_provider_form.steps.provider_details_step.if_unchecked_annotations_will_not")}
            />
          </div>
        </div>
      )}
    </div>
  );
};
