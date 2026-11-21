import { test, expect } from '@playwright/test'

test('资料、版本过滤、报告和任务历史可以在网页中使用',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message))
 await page.goto('/')
 await expect(page.getByRole('heading',{name:'让每次排障，都有据可查。'})).toBeVisible()
 await page.getByRole('button',{name:'加载演示案例'}).click()
 await expect(page.getByRole('textbox',{name:'诊断问题'})).toHaveValue(/SampleClient/)
 await page.getByRole('button',{name:'开始调查'}).click()
 await expect(page.getByText('本地检索 · 未调用模型')).toBeVisible()
 await expect(page.getByRole('heading',{name:'因版本约束排除的资料'})).toBeVisible()
 await expect(page.getByRole('link',{name:'下载 Markdown 报告'})).toBeVisible()
 await expect(page.getByRole('heading',{name:'可核对的来源'})).toBeVisible()
 await page.getByRole('button',{name:/运行记录/}).click()
 await expect(page.locator('.history-list')).toContainText('SampleClient')
 await page.locator('nav').getByRole('button',{name:/项目资料/}).click()
 await expect(page.locator('.source-list')).toContainText('migration-v2.md')
 await page.screenshot({path:'../.runtime/ui-desktop.png',fullPage:true})
 expect(errors).toEqual([])
})

test('手机宽度保持可用布局',async({page})=>{
 await page.setViewportSize({width:390,height:844})
 await page.goto('/')
 await expect(page.getByRole('heading',{name:'让每次排障，都有据可查。'})).toBeVisible()
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true)
 await page.screenshot({path:'../.runtime/ui-mobile.png',fullPage:true})
})
