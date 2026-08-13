/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Dynamic Fsync Driver
 * Based on faux123 / flar2 Dynamic Fsync implementations
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kobject.h>
#include <linux/sysfs.h>
#include <linux/workqueue.h>
#include <linux/writeback.h>
#include <linux/msm_drm_notify.h>
#include <linux/dynamic_fsync.h>

#define DYN_FSYNC_VERSION "2.0"

bool dynamic_fsync_active = true;
EXPORT_SYMBOL(dynamic_fsync_active);

static bool dyn_fsync_enabled = true;
static struct workqueue_struct *dyn_fsync_wq;
static struct work_struct dyn_fsync_work;

static void dyn_fsync_sync_work(struct work_struct *work)
{
	emergency_sync();
}

static int dyn_fsync_drm_notifier_cb(struct notifier_block *nb,
				     unsigned long event, void *data)
{
	struct msm_drm_notifier *evdata = data;
	int *blank;

	if (!evdata || !evdata->data)
		return 0;

	blank = evdata->data;

	if (event == MSM_DRM_EARLY_EVENT_BLANK || event == MSM_DRM_EVENT_BLANK) {
		if (*blank == MSM_DRM_BLANK_POWERDOWN) {
			dynamic_fsync_active = false;
			if (dyn_fsync_enabled && dyn_fsync_wq)
				queue_work(dyn_fsync_wq, &dyn_fsync_work);
		} else if (*blank == MSM_DRM_BLANK_UNBLANK) {
			if (dyn_fsync_enabled)
				dynamic_fsync_active = true;
		}
	}

	return 0;
}

static struct notifier_block dyn_fsync_drm_nb = {
	.notifier_call = dyn_fsync_drm_notifier_cb,
};

static ssize_t dyn_fsync_active_show(struct kobject *kobj,
				     struct kobj_attribute *attr, char *buf)
{
	return sprintf(buf, "%d\n", dyn_fsync_enabled ? 1 : 0);
}

static ssize_t dyn_fsync_active_store(struct kobject *kobj,
				      struct kobj_attribute *attr,
				      const char *buf, size_t count)
{
	unsigned int val;

	if (sscanf(buf, "%u", &val) != 1)
		return -EINVAL;

	dyn_fsync_enabled = (val != 0);
	dynamic_fsync_active = dyn_fsync_enabled;

	if (!dyn_fsync_enabled && dyn_fsync_wq)
		queue_work(dyn_fsync_wq, &dyn_fsync_work);

	return count;
}

static ssize_t dyn_fsync_version_show(struct kobject *kobj,
				      struct kobj_attribute *attr, char *buf)
{
	return sprintf(buf, "%s\n", DYN_FSYNC_VERSION);
}

static struct kobj_attribute dyn_fsync_active_attr =
	__ATTR(Dyn_fsync_active, 0644, dyn_fsync_active_show, dyn_fsync_active_store);

static struct kobj_attribute dyn_fsync_active_lower_attr =
	__ATTR(dyn_fsync_active, 0644, dyn_fsync_active_show, dyn_fsync_active_store);

static struct kobj_attribute dyn_fsync_version_attr =
	__ATTR(dyn_fsync_version, 0444, dyn_fsync_version_show, NULL);

static struct attribute *dyn_fsync_attrs[] = {
	&dyn_fsync_active_attr.attr,
	&dyn_fsync_active_lower_attr.attr,
	&dyn_fsync_version_attr.attr,
	NULL,
};

static struct attribute_group dyn_fsync_attr_group = {
	.attrs = dyn_fsync_attrs,
};

static struct kobject *dyn_fsync_kobj;

static int __init dynamic_fsync_init(void)
{
	int ret;

	dyn_fsync_wq = create_singlethread_workqueue("dyn_fsync_wq");
	if (!dyn_fsync_wq)
		pr_err("dyn_fsync: failed to create workqueue\n");

	INIT_WORK(&dyn_fsync_work, dyn_fsync_sync_work);

	dyn_fsync_kobj = kobject_create_and_add("dyn_fsync", kernel_kobj);
	if (dyn_fsync_kobj) {
		ret = sysfs_create_group(dyn_fsync_kobj, &dyn_fsync_attr_group);
		if (ret) {
			pr_err("dyn_fsync: failed to create sysfs group\n");
			kobject_put(dyn_fsync_kobj);
		}
	}

	ret = msm_drm_register_client(&dyn_fsync_drm_nb);
	if (ret)
		pr_err("dyn_fsync: failed to register DRM notifier: %d\n", ret);

	pr_info("Dynamic Fsync version %s initialized\n", DYN_FSYNC_VERSION);
	return 0;
}

static void __exit dynamic_fsync_exit(void)
{
	msm_drm_unregister_client(&dyn_fsync_drm_nb);

	if (dyn_fsync_kobj)
		kobject_put(dyn_fsync_kobj);

	if (dyn_fsync_wq) {
		flush_workqueue(dyn_fsync_wq);
		destroy_workqueue(dyn_fsync_wq);
	}
}

module_init(dynamic_fsync_init);
module_exit(dynamic_fsync_exit);

MODULE_AUTHOR("faux123 / flar2 / AntiGravity");
MODULE_DESCRIPTION("Dynamic Fsync Driver for Android");
MODULE_LICENSE("GPL v2");
