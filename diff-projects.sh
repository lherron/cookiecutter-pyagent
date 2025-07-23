python ../sync_cookiecutter_template.py \
    --template-dir "src" \
    --expanded-dir ../../evaitools/src \
    --var project_slug="daily_obsidian_template" \
    --var agent_name="DailyObsidianTemplateAgent" \
    --var "__gh_slug"="lherron/daily-obsidian-template" \
    --var project_name="daily-obsidian-template"




python ../sync_cookiecutter_template.py \
    --template-dir . \
    --expanded-dir ../simple-calc \
    --var project_slug="simple_calc" \
    --var agent_name="SimpleCalcAgent" \
    --var "__gh_slug"="lherron/simple-calc" \
    --var project_name="simple-calc" \
    --var description="A description of my awesome package" \
    --diff-only