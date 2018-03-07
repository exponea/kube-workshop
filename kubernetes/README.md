Kubernetes workshop
===================

1. Making sure everyone installed `minikube` and `kubectl` and its working.
---------------------------------------------------------------------------

Goals:

 - make sure everyone is ready to start workshop and have all prerequisites
 - explain `minikube` and `kubectl`

Bash aliases you can add to your `~/.bash_profile`:
```
# k alias to kubectl
alias k='kubectl'
# autocomplete for k (alias to kubectl)
source <(kubectl completion bash | sed 's/kubectl/k/g')
```

Links:

 - installation [https://github.com/kubernetes/minikube/blob/v0.25.0/README.md](https://github.com/kubernetes/minikube/blob/v0.25.0/README.md)
 - minikube download [https://github.com/kubernetes/minikube/releases](https://github.com/kubernetes/minikube/releases)
 - minikube drivers [https://github.com/kubernetes/minikube/blob/master/docs/drivers.md](https://github.com/kubernetes/minikube/blob/master/docs/drivers.md)

2. What is container and what is a pod?
---------------------

Goals:

 - explain basic concepts

Links:

 - container or a single image [https://kubernetes.io/docs/concepts/containers/images/](https://kubernetes.io/docs/concepts/containers/images/)
 - understanding pod https://kubernetes.io/docs/concepts/workloads/pods/pod-overview/#understanding-pods

3. Creating your first deployment.
-------------------

Goals:

 - write a deployment spec file
 - create and inspect deployment
 - interact with deployment remotely using `kubectl`

Create deployment.yml

```
---
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: flask-demo
  labels:
    app: flask-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: flask-demo
  template:
    metadata:
      labels:
        app: flask-demo
    spec:
      containers:
      - name: flask-demo
        image: exponea/flask-demo:1.0
        command: ["python", "runner.py"]

```

Useful commands:

```
kubectl explain deployment
kubectl apply -f demo-deployment.yaml
kubectl get pods
kubectl describe pod <POD>
kubectl logs <POD>
kubectl exec <POD> -- ps axu
kubectl delete <POD>
kubectl port-forward <POD> 9090:80  # exposing pod to your local machine
```

Links:

 - creating a deployment [https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#creating-a-deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#creating-a-deployment)

4. Service resource.
--------------------

Goals:

 - create a service
 - use label selectors to expose a pod externally
 - headless service, node port and loadbalancer

Create service.yml

```
---
apiVersion: v1
kind: Service
metadata:
  name: flask-demo
  labels:
    app: flask-demo
spec:
  ports:
  - port: 80
    name: http
    targetPort: 80
  selector:
    app: flask-demo
```

Useful commands:

```
kubectl explain service
kubectl get service
kubectl describe service <SVC>
kubectl get endpoint
kubectl describe endpoint <EP>
```

Check service with curl: `kubectl run curl --image=tutum/curl -it --rm`

Links:

 - defining a service [https://kubernetes.io/docs/concepts/services-networking/service/#defining-a-service](https://kubernetes.io/docs/concepts/services-networking/service/#defining-a-service)

5. Ingress.
----------

Goals:

 - explain why do we need ingress
 - differences between cloud providers and minikube
 - setup ingress and loadbalancer in minikube

Create ingress.yml

```
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: flask-demo
spec:
  rules:
  - host: flask.demo
    http:
      paths:
      - backend:
          serviceName: flask-demo
          servicePort: 80
```

Useful commands:

```
minikube addons enable ingress  # setup nginx lb in minikube
minikube service list  # list all services with urls in local cluster
minikube ip
```

To simulate dns, add IP from `minikube ip` to /etc/hosts and you can access http://flask.demo from your browser.

```
echo $(minikube ip) flask.demo | sudo tee -a /etc/hosts
```

Links:

 - [https://kubernetes.io/docs/concepts/services-networking/ingress/](https://kubernetes.io/docs/concepts/services-networking/ingress/)

6. Rolling update, scaling.
--------------------------

Goals:

 - show rolling update deployment and scaling
 - migrate app to version `2.0`
 - mention various deployment strategies

Modify deployment.yml, add following lines under `spec` section:

```
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

* deployment is rolled out only if you change `spec.template`
* deployment will stop if it encounter some error, can’t pull image, health check etc.

Useful commands:

```
kubectl rollout status deployment/flask-demo
kubectl scale deployment flask-demo --replicas=5
```

Links:

 - [https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#updating-a-deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#updating-a-deployment)

7. Config map.
---------------

Goals:

 - create ConfigMaps to store application configuration data
 - prepare config for redis we will use in our application

Create redis.yml
```
---
apiVersion: v1
kind: ConfigMap
metadata:
 name: redis-conf
data:
 redis.conf: |+
   appendonly yes
   protected-mode no
   bind 0.0.0.0
   port 6379
   dir /var/lib/redis
```

Commands:
```
kubectl explain configmap
kubectl create configmap redis-conf --from-file redis.conf  # create directly from file
```

Links:

 - [https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/#create-a-configmap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/#create-a-configmap)

8. Stateful set.
----------------

Goals:

 - create StatefulSet to provision redis database (stateful application)
 - explain ordinal index, stable network id, stable storage, deployment and scaling guarantees

Append to redis.yml

```
---
apiVersion: v1
kind: Service
metadata:
  labels:
    app: redis
  name: redis
spec:
  ports:
    - name: redis
      protocol: TCP
      port: 6379
      targetPort: 6379
  selector:
    app: redis

---
apiVersion: apps/v1beta1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 1
  template:
    metadata:
      labels:
        app: redis
    spec:
      terminationGracePeriodSeconds: 10
      containers:
        - name: redis
          image: redis:4.0.8-alpine
          command:
            - redis-server
          args:
            - /etc/redis/redis.conf
          resources:
            requests:
              cpu: 100m
              memory: 100Mi
          ports:
            - containerPort: 6379
              name: redis
          volumeMounts:
            - name: redis-data
              mountPath: /var/lib/redis
            - name: redis-conf
              mountPath: /etc/redis
      volumes:
        - name: redis-conf
          configMap:
             name: redis-conf
             items:
              - key: redis.conf
                path: redis.conf
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Mi
```

Links:

 - stateful sets [https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
 - persistent volumes [https://kubernetes.io/docs/concepts/storage/persistent-volumes/](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

9. Managing app configuration and secret.
---------------------------------------

Goals:

 - explain secrets
 - setup environment variables required in new app release
 - use secrets to store env variable with password
 - migrate app to version `3.0`

Setup environment variable in deployment.yml. Add following code under `spec.template.spec.containers`:

```
        env:
        - name: REDIS_URL
          value: redis://redis:6379/0
```

Create secrets.yml containing password:
```
---
apiVersion: v1
kind: Secret
metadata:
  name: flask-demo
type: Opaque
data:
  AUTH: YWRtaW46YWRtaW4=
```


Secrets must be Base64 encoded string:
```
echo -n admin:admin | base64
```

Again update deployment.yml and add extra to `spec.template`:
```
        envFrom:
        - secretRef:
            name: flask-demo
```

Deploy app version `3.0`.

Links:

 - environment variables [https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container](https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container)
 - secrets [https://kubernetes.io/docs/concepts/configuration/secret/#creating-your-own-secrets](https://kubernetes.io/docs/concepts/configuration/secret/#creating-your-own-secrets)

10. Monitoring and Health Checks.
--------------------------------

Goals:

 - create pods with readiness and liveness probes
 - troubleshoot failing readiness and liveness probes
 - kubectl explain `spec.template.spec.containers.readinessProbe` (what is the difference… http, exec command, tcp socket)

Modify deployment.yml and add following code under `spec.template.spec.containers` section:
```
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
```

The same with redis.yml:
```
          livenessProbe:
            exec:
              command:
              - sh
              - -c
              - "redis-cli -h $(hostname) ping"
            initialDelaySeconds: 15
            timeoutSeconds: 5
```

Links:

 - [https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-probes/](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-probes/)

11. Resources.
------------

Goals:

 - explain resource management
 - setup resource consumption and limits for our deployment

Commands:
```
kubectl explain deployment.spec.template.spec.containers.resources
```

Similar to probes, add to `deployment.yml` under `spec.template.spec.containers` this block:
```
        resources:
          limits:
            cpu: "1"
            memory: 128Mi
          requests:
            cpu: "50m"
            memory: 32Mi
```

Links:

 - [https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/)

12. Prometheus + Grafana.
------------------------

Goals:

 - setup Prometheus and Grafana
 - migrate app to version `4.0`
 - setup service monitor
 - show example dashboard and graphs


To setup Prometheus with Grafana run this command:
```
kubernetes/prometheus/deploy
```

Deploy app version `4.0` with `/metrics` endpoint for monitoring.

Setup service monitor for app with command:
```
kubectl apply -f service-monitor.yml --namespace=monitoring
```

Example Grafana metrics:
```
Requests per second:
  sum(rate(request_count[1m])) by (http_status, method, exported_endpoint)

Memory usage:
  process_resident_memory_bytes{job="flask-demo"}

Cpu usage:
  rate(process_cpu_seconds_total{job="flask-demo"}[3m]) * 100

Open file descriptors:
  process_open_fds{job="flask-demo"}
```

13. Kubernetes dashboard.
---------------------------

Run `minikube dashboard`.
