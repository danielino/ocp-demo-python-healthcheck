
openshift-newbuild:
	oc new-build --strategy docker --binary --name healthcheck-demo

openshift-build:
	oc start-build healthcheck-demo --from-dir . --follow

openshift-deploy:
	oc new-app healthcheck-demo
