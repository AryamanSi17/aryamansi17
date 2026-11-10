#!/usr/bin/env bash
# Pull the contribution calendar + top repos into data/contributions.json (needs gh, GITHUB_TOKEN).
set -euo pipefail
cd "$(dirname "$0")/.."
LOGIN="${1:-AryamanSi17}"
gh api graphql -f login="$LOGIN" -f query='
query($login:String!){ user(login:$login){
  repositories(first:6,orderBy:{field:STARGAZERS,direction:DESC},ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false){
    totalCount nodes{name description stargazerCount url primaryLanguage{name color}}}
  contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
}}' > data/contributions.json
echo "wrote data/contributions.json ($(python3 -c "import json;print(json.load(open('data/contributions.json'))['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions'])") contributions)"
