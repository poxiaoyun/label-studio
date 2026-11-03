import { Button } from "@humansignal/ui";
import { cn } from "apps/labelstudio/src/utils/bem";
import type { FC } from "react";
import "./EmptyList.scss";
import { HeidiAi } from "apps/labelstudio/src/assets/images";
import { t } from "@humansignal/i18n";

export const EmptyList: FC = () => {
  return (
    <div className={cn("empty-models-list").toClassName()}>
      <div className={cn("empty-models-list").elem("content").toClassName()}>
        <div className={cn("empty-models-list").elem("heidy").toClassName()}>
          <HeidiAi />
        </div>
        <div className={cn("empty-models-list").elem("title").toClassName()}>{t("pages.models.components.empty_list.create_a_model")}</div>
        <div className={cn("empty-models-list").elem("caption").toClassName()}>
          {t("pages.models.components.empty_list.build_a_high_quality_model")}
        </div>
        <Button aria-label={t("pages.models.components.empty_list.create_new_model")}>{t("pages.models.components.empty_list.create_a_model")}</Button>
      </div>
    </div>
  );
};
