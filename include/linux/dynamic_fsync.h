/* SPDX-License-Identifier: GPL-2.0 */
#ifndef _LINUX_DYNAMIC_FSYNC_H
#define _LINUX_DYNAMIC_FSYNC_H

#include <linux/types.h>

#ifdef CONFIG_DYNAMIC_FSYNC
extern bool dynamic_fsync_active;
#else
#define dynamic_fsync_active false
#endif

#endif /* _LINUX_DYNAMIC_FSYNC_H */
