set -e

mongo <<EOF
db = db.getSiblingDB('arch')
db.createCollection('users')
db.orders.createIndex({"id": -1}) 
EOF