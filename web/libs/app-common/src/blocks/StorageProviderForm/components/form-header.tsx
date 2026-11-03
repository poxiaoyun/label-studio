import { Button } from "@humansignal/ui";
import { IconCross } from "@humansignal/icons";
import { t } from "@humansignal/i18n";

interface FormHeaderProps {
  title?: string;
  onClose: () => void;
}

export const FormHeader = ({ title, onClose }: FormHeaderProps) => {
  return (
    <div className="flex justify-between items-start px-wide py-base pt-wide">
      <div>
        <h2 className="m-0 mb-tight text-headline-large font-medium text-neutral-content">{title}</h2>
        <div className="text-body-medium text-neutral-content-subtle leading-relaxed">
          {t("appcommon.storage_provider_form.components.form_header.import_your_data_from_cloud")}
        </div>
      </div>
      <Button leading={<IconCross />} look="string" onClick={onClose} />
    </div>
  );
};
