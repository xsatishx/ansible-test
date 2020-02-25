echo "Have you setup password less access from this node to k8s masters and workers?"
echo "If not please read the README.md"
echo "sleep 2s"

echo "Preconfiguring the nodes..."
ansible-playbook  -i hosts preconfig.yaml

echo "Installing the dependencies..."
ansible-playbook -i hosts k8s-depends.yaml

echo "Setting up k8s master node ..."
ansible-playbook -i hosts master-setup.yaml

echo "Setting up k8s worker node ..."
ansible-playbook -i hosts workers-setup.yaml

