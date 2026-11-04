import React from "react";
import { Spinner } from "../../../components";
import { useAPI } from "../../../providers/ApiProvider";
import { cn } from "../../../utils/bem";
import "./Config.scss";
import { IconInfo } from "@humansignal/icons";
import { Button, EnterpriseBadge } from "@humansignal/ui";
import { t, tTemplate } from "@humansignal/i18n";

const listClass = cn("templates-list");

const Arrow = () => (
  <svg width="8" height="12" viewBox="0 0 8 12" fill="none" xmlns="http://www.w3.org/2000/svg">
    <title>{t("pages.create_project.config.templates_list.arrow_icon")}</title>
    <path opacity="0.9" d="M2 10L6 6L2 2" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
  </svg>
);

const TemplatesInGroup = ({ templates, group, onSelectRecipe, isEdition }) => {
  const picked = templates
    .filter((recipe) => recipe.group === group)
    // templates without `order` go to the end of the list
    .sort((a, b) => (a.order ?? Number.POSITIVE_INFINITY) - (b.order ?? Number.POSITIVE_INFINITY));

  const isCommunityEdition = isEdition === "Community";

  return (
    <ul>
      {picked.map((recipe) => {
        const isEnterpriseTemplate = recipe.type === "enterprise";
        const isDisabled = isCommunityEdition && isEnterpriseTemplate;

        return (
          <li
            key={recipe.title}
            onClick={() => !isDisabled && onSelectRecipe(recipe)}
            className={listClass.elem("template").mod({ disabled: isDisabled }).toClassName()}
            title={isDisabled ? t("templates.enterprise_tooltip") : ""}
          >
            <img src={recipe.image} alt={""} />
            <div className="flex flex-col items-center w-full">
              <h3 className="flex flex-1 justify-center text-center w-full">{tTemplate(recipe.title)}</h3>
              {isEnterpriseTemplate && isCommunityEdition && <EnterpriseBadge className="mb-base" />}
            </div>
          </li>
        );
      })}
    </ul>
  );
};

export const TemplatesList = ({ selectedGroup, selectedRecipe, onCustomTemplate, onSelectGroup, onSelectRecipe }) => {
  const [groups, setGroups] = React.useState([]);
  const [templates, setTemplates] = React.useState();
  const api = useAPI();
  const isEdition = window?.APP_SETTINGS?.version_edition;

  React.useEffect(() => {
    const fetchData = async () => {
      const res = await api.callApi("configTemplates");

      if (!res) return;
      const { templates, groups } = res;

      setTemplates(templates);
      setGroups(groups);
    };
    fetchData();
  }, []);

  // [pxs] the picker only offers templates this build can actually use:
  // enterprise-only entries would just render disabled
  const visibleTemplates = React.useMemo(
    () => (templates || []).filter((recipe) => recipe.type !== "enterprise"),
    [templates],
  );
  const visibleGroups = React.useMemo(
    () => groups.filter((group) => visibleTemplates.some((recipe) => recipe.group === group)),
    [groups, visibleTemplates],
  );

  const selected = selectedGroup && visibleGroups.includes(selectedGroup) ? selectedGroup : visibleGroups[0];

  return (
    <div className={listClass}>
      <aside className={listClass.elem("sidebar").toClassName()}>
        <ul>
          {visibleGroups.map((group) => (
            <li
              key={group}
              onClick={() => onSelectGroup(group)}
              className={listClass
                .elem("group")
                .mod({
                  active: selected === group,
                  selected: selectedRecipe?.group === group,
                })
                .toClassName()}
            >
              {tTemplate(group)}
              <Arrow />
            </li>
          ))}
        </ul>
        <Button
          type="button"
          align="left"
          look="string"
          size="small"
          onClick={onCustomTemplate}
          className="w-full"
          aria-label={t("pages.create_project.config.templates_list.create_custom_template")}
        >
          {t("pages.create_project.config.templates_list.custom_template")}
        </Button>
      </aside>
      <main>
        {!templates && <Spinner style={{ width: "100%", height: 200 }} />}
        <TemplatesInGroup
          templates={visibleTemplates}
          group={selected}
          onSelectRecipe={onSelectRecipe}
          isEdition={isEdition}
        />
      </main>
      <footer className="flex items-center justify-center gap-1">
        <IconInfo className={listClass.elem("info-icon").toClassName()} width="20" height="20" />
        <span>
          {t("pages.create_project.config.templates_list.see_the_documentation_to")}{" "}
          <a href="https://labelstud.io/guide" target="_blank" rel="noreferrer">
            {t("templates.footer.contribute")}
          </a>
          .
        </span>
      </footer>
    </div>
  );
};
